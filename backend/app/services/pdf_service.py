import os
import pymupdf as fitz
import logging
from typing import Dict, List, Any, Optional
from PIL import Image
import io
from app.config import settings
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

class PDFService:
    def extract_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """
        Parses a PDF using PyMuPDF.
        Preserves original pages, text blocks, coordinates, typography, tables, and images.
        """
        doc = fitz.open(file_path)
        page_count = len(doc)
        toc = doc.get_toc()  # [[lvl, title, page], ...]
        pages_data = []
        full_text = []

        doc_media_dir = os.path.join(settings.EXTRACTED_MEDIA_DIR, document_id)
        os.makedirs(doc_media_dir, exist_ok=True)

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_num = page_idx + 1
            rect = page.rect
            width, height = rect.width, rect.height

            # Render page image for authentic original source display
            page_img_filename = f"page_{page_num}.png"
            page_img_path = os.path.join(doc_media_dir, page_img_filename)
            rel_page_img_path = f"/api/media/{document_id}/{page_img_filename}"
            if not os.path.exists(page_img_path):
                pix = page.get_pixmap(dpi=150)
                pix.save(page_img_path)

            # Extract structured blocks with typography
            text_dict = page.get_text("dict")
            blocks = []
            page_text_pieces = []

            for block in text_dict.get("blocks", []):
                b_type = block.get("type", 0)  # 0 for text, 1 for image
                bbox = block.get("bbox", [0, 0, 0, 0])
                
                if b_type == 0:  # Text block
                    lines = []
                    block_text_lines = []
                    max_font_size = 0.0
                    is_bold = False

                    line_details = []
                    for line in block.get("lines", []):
                        line_text = ""
                        line_font_size = 0.0
                        line_is_bold = False
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            font_size = span.get("size", 10.0)
                            flags = span.get("flags", 0)
                            if font_size > line_font_size:
                                line_font_size = font_size
                            if font_size > max_font_size:
                                max_font_size = font_size
                            if flags & 2 != 0 or "bold" in span.get("font", "").lower():
                                line_is_bold = True
                                is_bold = True
                            line_text += span_text
                        clean_line = line_text.strip()
                        if clean_line:
                            block_text_lines.append(clean_line)
                            line_details.append({
                                "text": clean_line,
                                "font_size": line_font_size,
                                "is_bold": line_is_bold,
                            })

                    block_text = "\n".join(block_text_lines).strip()
                    if block_text:
                        blocks.append({
                            "type": "TEXT",
                            "bbox": bbox,
                            "text": block_text,
                            "max_font_size": max_font_size,
                            "is_bold": is_bold,
                            "lines": line_details,
                        })
                        page_text_pieces.append(block_text)

                elif b_type == 1:  # Image block
                    blocks.append({
                        "type": "IMAGE",
                        "bbox": bbox,
                        "text": "[Image/Diagram]",
                        "max_font_size": 0,
                        "is_bold": False,
                    })

            # Detect native tables if supported
            tables_data = []
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for tbl_idx, table in enumerate(tables.tables):
                        df = table.extract()
                        html_table = self._convert_table_to_html(df)
                        tables_data.append({
                            "bbox": table.bbox,
                            "html": html_table,
                            "raw": df,
                        })
            except Exception as e:
                logger.debug(f"Table extraction on page {page_num} had no tables or error: {e}")

            # Check if text is insufficient (scanned document)
            raw_page_text = "\n".join(page_text_pieces).strip()
            if len(raw_page_text) < 30 and ocr_service.is_available():
                logger.info(f"Page {page_num} has minimal text. Running OCR fallback.")
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = ocr_service.ocr_image(img)
                if ocr_text:
                    raw_page_text = ocr_text
                    blocks.append({
                        "type": "TEXT",
                        "bbox": [0, 0, width, height],
                        "text": ocr_text,
                        "max_font_size": 11.0,
                        "is_bold": False,
                    })

            full_text.append(f"--- Page {page_num} ---\n{raw_page_text}")
            pages_data.append({
                "page_number": page_num,
                "width": width,
                "height": height,
                "page_image": rel_page_img_path,
                "blocks": blocks,
                "tables": tables_data,
                "text": raw_page_text,
            })

        doc.close()

        return {
            "page_count": page_count,
            "toc": toc,
            "pages": pages_data,
            "full_text": "\n\n".join(full_text),
        }

    def _convert_table_to_html(self, rows: List[List[Any]]) -> str:
        if not rows:
            return ""
        html = ["<table class='min-w-full border border-gray-300 divide-y divide-gray-200 text-sm'>"]
        header = rows[0]
        html.append("<thead class='bg-gray-50'><tr>")
        for cell in header:
            cell_str = str(cell).strip() if cell is not None else ""
            html.append(f"<th class='px-3 py-2 text-left font-semibold text-gray-700 border-b'>{cell_str}</th>")
        html.append("</tr></thead>")
        html.append("<tbody class='divide-y divide-gray-200 bg-white'>")
        for row in rows[1:]:
            html.append("<tr>")
            for cell in row:
                cell_str = str(cell).strip() if cell is not None else ""
                html.append(f"<td class='px-3 py-2 border-b text-gray-800'>{cell_str}</td>")
            html.append("</tr>")
        html.append("</tbody></table>")
        return "".join(html)

pdf_service = PDFService()
