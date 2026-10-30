import logging
import re
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

        current_topic_idx = None  # None indicates preamble (before Topic 1 starts)
        element_orders = {t.id: 0 for t in topics}
        added_full_pages = set()

        def is_running_header_footer(text: str) -> bool:
            clean = text.strip().lower()
            if re.match(r'^(?:page\s+\d+|\d+)$', clean):
                return True
            if 'class notes' in clean or 'lecture notes' in clean:
                return True
            if re.match(r'^unit\s+[ivx\d]+\s*-\s*', clean):
                return True
            if clean in ('unit iii', 'mobile network layer', 'contents'):
                return True
            return False

        try:
            first_topic_start = int(topics[0].source_start) if topics and topics[0].source_start and topics[0].source_start.isdigit() else 1
        except Exception:
            first_topic_start = 1

        for page in pages:
            p_num = page.get("page_number", 1)
            blocks = page.get("blocks", [])

            # Before first topic start page, all pages are cover / table of contents
            if p_num < first_topic_start:
                continue

            for block in blocks:
                b_type = block.get("type", "TEXT")
                b_text = block.get("text", "")
                bbox = block.get("bbox", [0, 0, 0, 0])

                # Check if this block triggers transition to next topic (or topic 0 if in preamble)
                target_idx = 0 if current_topic_idx is None else current_topic_idx + 1
                if target_idx < len(topics):
                    target_topic = topics[target_idx]
                    try:
                        target_start_p = int(target_topic.source_start) if target_topic.source_start and target_topic.source_start.isdigit() else p_num
                    except Exception:
                        target_start_p = p_num

                    if p_num >= target_start_p:
                        num_match = re.match(r'^(\d+(?:\.\d+)*)', target_topic.name)
                        num_prefix = num_match.group(1) if num_match else ""
                        title_part = re.sub(r'^\d+(?:\.\d+)*\s*', '', target_topic.name).strip().lower()
                        clean_bt = re.sub(r'[^a-z0-9]', '', b_text.lower())
                        clean_title = re.sub(r'[^a-z0-9]', '', title_part)

                        matches_heading = False
                        if num_prefix and num_prefix in b_text and clean_title[:10] in clean_bt:
                            matches_heading = True
                        elif clean_title and len(clean_title) >= 5 and clean_title[:20] in clean_bt:
                            matches_heading = True

                        if matches_heading:
                            current_topic_idx = target_idx

                # If still in preamble (before Topic 1 heading), do not assign to any topic
                if current_topic_idx is None:
                    continue

                curr_topic = topics[current_topic_idx]
                e_order = element_orders[curr_topic.id]

                # Filter out pure running headers/footers
                if b_type == "TEXT" and is_running_header_footer(b_text):
                    continue

                # Attach FULL_PAGE reference for viewer (with empty content_text so it never acts as a text note)
                fp_key = (curr_topic.id, p_num)
                if fp_key not in added_full_pages and page.get("page_image"):
                    added_full_pages.add(fp_key)
                    r_fp = SourceRegion(
                        document_id=document.id,
                        topic_id=curr_topic.id,
                        page_number=p_num,
                        region_type="FULL_PAGE",
                        element_order=e_order,
                        source_reference=f"Page {p_num}",
                        media_path=page.get("page_image"),
                        content_text="",  # Clean: not a text note
                    )
                    db.add(r_fp)
                    regions.append(r_fp)
                    e_order += 1

                media_path = block.get("media_path") if b_type == "IMAGE" else None
                fig_caption = block.get("caption") if b_type == "IMAGE" else None
                src_ref = fig_caption if fig_caption else (f"Page {p_num} Diagram" if b_type == "IMAGE" else f"Page {p_num}")
                content_text = fig_caption if (b_type == "IMAGE" and fig_caption) else b_text

                r = SourceRegion(
                    document_id=document.id,
                    topic_id=curr_topic.id,
                    page_number=p_num,
                    region_type=b_type,
                    x1=float(bbox[0]),
                    y1=float(bbox[1]),
                    x2=float(bbox[2]),
                    y2=float(bbox[3]),
                    element_order=e_order,
                    source_reference=src_ref,
                    media_path=media_path,
                    content_text=content_text,
                )
                db.add(r)
                regions.append(r)
                e_order += 1
                element_orders[curr_topic.id] = e_order

            # Add tables for this page to current topic
            if current_topic_idx is not None:
                for tbl in page.get("tables", []):
                    curr_topic = topics[current_topic_idx]
                    e_order = element_orders[curr_topic.id]
                    bbox = tbl.get("bbox", [0, 0, 0, 0])
                    r_tbl = SourceRegion(
                        document_id=document.id,
                        topic_id=curr_topic.id,
                        page_number=p_num,
                        region_type="TABLE",
                        x1=float(bbox[0]),
                        y1=float(bbox[1]),
                        x2=float(bbox[2]),
                        y2=float(bbox[3]),
                        element_order=e_order,
                        source_reference=f"Page {p_num} Table",
                        content_html=tbl.get("html", ""),
                        content_text="Table content on page " + str(p_num),
                    )
                    db.add(r_tbl)
                    regions.append(r_tbl)
                    element_orders[curr_topic.id] = e_order + 1

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
                        content_text=el.get("visual_content", el.get("text", "")),
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
                media_path=el.get("media_path"),
            )
            db.add(r)
            regions.append(r)
            element_order += 1

        db.commit()
        return regions

source_region_service = SourceRegionService()
