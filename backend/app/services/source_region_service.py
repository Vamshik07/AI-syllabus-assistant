import logging
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models.models import Document, Topic, Subtopic, SourceRegion

logger = logging.getLogger(__name__)

class SourceRegionService:
    def map_source_regions(
        self,
        db: Session,
        document: Document,
        topics: List[Topic],
        parsed_doc: Dict[str, Any]
    ) -> List[SourceRegion]:
        """
        Maps elements from parsed document into SourceRegion records for each Topic/Subtopic.
        Preserves original document layout, images, tables, coordinates, and sequential element ordering.
        """
        created_regions = []
        file_type = document.file_type.upper()

        if file_type == "PDF":
            created_regions = self._map_pdf_regions(db, document, topics, parsed_doc)
        elif file_type == "PPTX":
            created_regions = self._map_pptx_regions(db, document, topics, parsed_doc)
        elif file_type == "DOCX":
            created_regions = self._map_docx_regions(db, document, topics, parsed_doc)

        return created_regions

    def _map_pdf_regions(
        self,
        db: Session,
        document: Document,
        topics: List[Topic],
        parsed_doc: Dict[str, Any]
    ) -> List[SourceRegion]:
        pages = parsed_doc.get("pages", [])
        regions = []
        if not topics:
            return regions

        total_pages = len(pages)
        # Determine topic page ranges
        topic_page_ranges = []
        for i, t in enumerate(topics):
            try:
                start_p = int(t.source_start) if t.source_start and t.source_start.isdigit() else 1
            except Exception:
                start_p = 1
            
            if i + 1 < len(topics):
                try:
                    next_p = int(topics[i + 1].source_start) if topics[i + 1].source_start and topics[i + 1].source_start.isdigit() else start_p
                    end_p = max(start_p, next_p - 1 if next_p > start_p else start_p)
                except Exception:
                    end_p = start_p
            else:
                end_p = total_pages

            topic_page_ranges.append((t, start_p, end_p))

        # Assign elements to topics based on page ranges
        for topic, start_p, end_p in topic_page_ranges:
            element_order = 0
            for page in pages:
                p_num = page.get("page_number", 1)
                if start_p <= p_num <= end_p:
                    # 1. Full Page region for original visual rendering
                    page_img = page.get("page_image")
                    if page_img:
                        r = SourceRegion(
                            document_id=document.id,
                            topic_id=topic.id,
                            page_number=p_num,
                            region_type="FULL_PAGE",
                            element_order=element_order,
                            source_reference=f"Page {p_num}",
                            media_path=page_img,
                            content_text=page.get("text", ""),
                        )
                        db.add(r)
                        regions.append(r)
                        element_order += 1

                    # 2. Add detected tables as TABLE regions
                    for tbl in page.get("tables", []):
                        bbox = tbl.get("bbox", [0, 0, 0, 0])
                        r = SourceRegion(
                            document_id=document.id,
                            topic_id=topic.id,
                            page_number=p_num,
                            region_type="TABLE",
                            x1=float(bbox[0]),
                            y1=float(bbox[1]),
                            x2=float(bbox[2]),
                            y2=float(bbox[3]),
                            element_order=element_order,
                            source_reference=f"Page {p_num} Table",
                            content_html=tbl.get("html", ""),
                            content_text="Table content on page " + str(p_num),
                        )
                        db.add(r)
                        regions.append(r)
                        element_order += 1

                    # 3. Add text blocks
                    for block in page.get("blocks", []):
                        bbox = block.get("bbox", [0, 0, 0, 0])
                        b_type = block.get("type", "TEXT")
                        r = SourceRegion(
                            document_id=document.id,
                            topic_id=topic.id,
                            page_number=p_num,
                            region_type=b_type,
                            x1=float(bbox[0]),
                            y1=float(bbox[1]),
                            x2=float(bbox[2]),
                            y2=float(bbox[3]),
                            element_order=element_order,
                            source_reference=f"Page {p_num}, Block {element_order}",
                            content_text=block.get("text", ""),
                        )
                        db.add(r)
                        regions.append(r)
                        element_order += 1

        db.commit()
        return regions

    def _map_pptx_regions(
        self,
        db: Session,
        document: Document,
        topics: List[Topic],
        parsed_doc: Dict[str, Any]
    ) -> List[SourceRegion]:
        slides = parsed_doc.get("slides", [])
        regions = []

        # In PPTX, topics can span a range of slides (from source_start to source_end)
        for topic in topics:
            try:
                start_s = int(topic.source_start) if topic.source_start and topic.source_start.isdigit() else topic.order_index
                end_s = int(topic.source_end) if topic.source_end and topic.source_end.isdigit() else start_s
            except Exception:
                start_s = topic.order_index
                end_s = topic.order_index

            matching_slides = [s for s in slides if start_s <= s.get("slide_number", 0) <= end_s]
            if not matching_slides and slides:
                matching_slides = [slides[min(topic.order_index - 1, len(slides) - 1)]]

            element_order = 0
            for slide in matching_slides:
                # Add slide region
                r_slide = SourceRegion(
                    document_id=document.id,
                    topic_id=topic.id,
                    slide_number=slide.get("slide_number"),
                    region_type="SLIDE",
                    element_order=element_order,
                    source_reference=f"Slide {slide.get('slide_number')}: {slide.get('title')}",
                    content_text=slide.get("text", ""),
                )
                db.add(r_slide)
                regions.append(r_slide)
                element_order += 1

                for el in slide.get("elements", []):
                    r = SourceRegion(
                        document_id=document.id,
                        topic_id=topic.id,
                        slide_number=slide.get("slide_number"),
                        region_type=el.get("type", "TEXT"),
                        x1=el.get("x1"),
                        y1=el.get("y1"),
                        x2=el.get("x2"),
                        y2=el.get("y2"),
                        element_order=element_order,
                        source_reference=f"Slide {slide.get('slide_number')} Element",
                        content_text=el.get("text", ""),
                        content_html=el.get("html"),
                        media_path=el.get("media_path"),
                    )
                    db.add(r)
                    regions.append(r)
                    element_order += 1

        db.commit()
        return regions

    def _map_docx_regions(
        self,
        db: Session,
        document: Document,
        topics: List[Topic],
        parsed_doc: Dict[str, Any]
    ) -> List[SourceRegion]:
        elements = parsed_doc.get("elements", [])
        regions = []
        if not topics:
            return regions

        # Map DOCX elements to topics based on heading transitions
        topic_idx = 0
        current_topic = topics[0]
        element_order = 0

        for el in elements:
            text = el.get("text", "").strip()
            heading_level = el.get("heading_level", 0)

            # Check if this element matches the next topic's heading
            if topic_idx + 1 < len(topics):
                next_topic = topics[topic_idx + 1]
                if text and (text.lower() == next_topic.name.lower() or heading_level == 1):
                    topic_idx += 1
                    current_topic = next_topic
                    element_order = 0

            # Match subtopic if applicable
            matched_subtopic_id = None
            if current_topic.subtopics:
                for sub in current_topic.subtopics:
                    if text and text.lower() == sub.name.lower():
                        matched_subtopic_id = sub.id
                        break

            r = SourceRegion(
                document_id=document.id,
                topic_id=current_topic.id,
                subtopic_id=matched_subtopic_id,
                region_type=el.get("type", "TEXT"),
                element_order=element_order,
                source_reference=f"Doc Section: {el.get('style', 'Normal')}",
                content_text=text,
                content_html=el.get("html"),
            )
            db.add(r)
            regions.append(r)
            element_order += 1

        db.commit()
        return regions

source_region_service = SourceRegionService()
