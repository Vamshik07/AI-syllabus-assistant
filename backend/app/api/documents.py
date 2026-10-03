from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.models import Document
from app.schemas.schemas import DocumentStatusResponse, DocumentResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    topics_count = len(doc.topics) if doc.topics else 0
    return {
        "id": doc.id,
        "processing_status": doc.processing_status,
        "processing_error": doc.processing_error,
        "page_count": doc.page_count,
        "slide_count": doc.slide_count,
        "topics_count": topics_count,
    }

@router.post("/{document_id}/process", response_model=DocumentResponse)
def reprocess_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    doc = document_service.process_document(db, document_id)
    return doc
