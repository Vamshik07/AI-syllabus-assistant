import os
import uuid
import logging
from typing import Dict, Any, Tuple
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.models.models import Document, Topic, Subtopic, SourceRegion, TopicProgress, UnitProgress
from app.services.pdf_service import pdf_service
from app.services.pptx_service import pptx_service
from app.services.docx_service import docx_service
from app.services.structure_service import structure_service
from app.services.source_region_service import source_region_service

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx"}
ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",  # Office files are zip packages
    "application/octet-stream",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

class DocumentService:
    def validate_file_upload(self, file: UploadFile, content: bytes) -> str:
        """Validates file extension, size, MIME type and magic header signatures."""
        if not content or len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB.")

        filename = file.filename or ""
        _, ext = os.path.splitext(filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'. Only .pdf, .pptx, and .docx are supported."
            )

        # Magic signature verification
        if ext == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise HTTPException(status_code=400, detail="Invalid PDF file: corrupted or invalid file signature.")
            return "PDF"
        elif ext in {".pptx", ".docx"}:
            # PK zip header
            if not content.startswith(b"PK\x03\x04"):
                raise HTTPException(status_code=400, detail=f"Invalid {ext.upper()} file: corrupted or invalid zip container.")
            return ext[1:].upper()

        raise HTTPException(status_code=400, detail="Unsupported file format.")

    def save_and_create_document(self, db: Session, unit_id: str, file: UploadFile, content: bytes) -> Document:
        """Saves file to disk and creates Document record in database."""
        file_type = self.validate_file_upload(file, content)

        # Remove existing document for this unit if any
        existing_doc = db.query(Document).filter(Document.unit_id == unit_id).first()
        if existing_doc:
            db.delete(existing_doc)
            db.commit()

        safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            unit_id=unit_id,
            file_name=file.filename,
            file_type=file_type,
            file_size=len(content),
            file_path=file_path,
            processing_status="UPLOADED",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def process_document(self, db: Session, document_id: str) -> Document:
        """
        Executes the full document processing pipeline:
        PARSING -> STRUCTURE DETECTION -> SOURCE VALIDATION -> TOPIC CREATION -> SOURCE REGION MAPPING
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        doc.processing_status = "PROCESSING"
        db.commit()

        try:
            file_type = doc.file_type.upper()
            parsed_doc = {}

            if file_type == "PDF":
                parsed_doc = pdf_service.extract_document(doc.file_path, doc.id)
                doc.page_count = parsed_doc.get("page_count", 0)
            elif file_type == "PPTX":
                parsed_doc = pptx_service.extract_document(doc.file_path, doc.id)
                doc.slide_count = parsed_doc.get("slide_count", 0)
            elif file_type == "DOCX":
                parsed_doc = docx_service.extract_document(doc.file_path, doc.id)

            doc.extracted_text = parsed_doc.get("full_text", "")

            # Structure detection
            topics_data, status = structure_service.extract_structure(file_type, parsed_doc)
            if not topics_data:
                doc.processing_status = "FAILED"
                doc.processing_error = "Unable to extract structure from document."
                db.commit()
                return doc

            # Clear existing topics for this document
            db.query(Topic).filter(Topic.document_id == doc.id).delete()
            db.commit()

            # Create topics and subtopics
            created_topics = []
            for t_idx, t_data in enumerate(topics_data):
                topic = Topic(
                    document_id=doc.id,
                    name=t_data["name"],
                    order_index=t_data.get("order_index", t_idx + 1),
                    source_start=str(t_data.get("source_start", "1")),
                    source_end=str(t_data.get("source_end", "1")),
                    confidence=float(t_data.get("confidence", 1.0)),
                    status=status,
                )
                db.add(topic)
                db.flush()

                for s_idx, s_data in enumerate(t_data.get("subtopics", [])):
                    subtopic = Subtopic(
                        topic_id=topic.id,
                        name=s_data["name"],
                        order_index=s_data.get("order_index", s_idx + 1),
                        source_start=str(s_data.get("source_start", "1")),
                        source_end=str(s_data.get("source_end", "1")),
                        confidence=float(s_data.get("confidence", 1.0)),
                        status=status,
                    )
                    db.add(subtopic)

                created_topics.append(topic)

            db.commit()

            # Map source regions
            source_region_service.map_source_regions(db, doc, created_topics, parsed_doc)

            # Initialize UnitProgress & TopicProgress for all topics
            unit = doc.unit
            user = unit.subject.user
            if user:
                unit_prog = db.query(UnitProgress).filter(
                    UnitProgress.user_id == user.id,
                    UnitProgress.unit_id == unit.id
                ).first()
                if not unit_prog:
                    unit_prog = UnitProgress(
                        user_id=user.id,
                        unit_id=unit.id,
                        total_topics=len(created_topics),
                        topics_completed=0,
                        status="NOT_STARTED"
                    )
                    db.add(unit_prog)
                else:
                    unit_prog.total_topics = len(created_topics)

                # Initialize topic progress: first topic unlocked, subsequent locked
                for idx, t in enumerate(created_topics):
                    t_prog = db.query(TopicProgress).filter(
                        TopicProgress.user_id == user.id,
                        TopicProgress.topic_id == t.id
                    ).first()
                    init_status = "UNLOCKED" if idx == 0 else "LOCKED"
                    if not t_prog:
                        t_prog = TopicProgress(
                            user_id=user.id,
                            topic_id=t.id,
                            status=init_status,
                        )
                        db.add(t_prog)

                db.commit()

            doc.processing_status = "PROCESSED" if status == "VERIFIED" else "REVIEW_REQUIRED"
            db.commit()
            db.refresh(doc)
            return doc

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
            doc.processing_status = "FAILED"
            doc.processing_error = str(e)
            db.commit()
            return doc

document_service = DocumentService()
