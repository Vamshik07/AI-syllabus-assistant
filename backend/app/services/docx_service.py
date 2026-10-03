import os
import logging
from typing import Dict, List, Any
import docx
from app.config import settings

logger = logging.getLogger(__name__)

class DOCXService:
    def extract_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """
        Parses a DOCX file using python-docx.
        Preserves original document structure, native Heading 1/2/3 hierarchies,
        paragraphs, tables, images, and exact sequential ordering.
        """
        doc = docx.Document(file_path)
        doc_media_dir = os.path.join(settings.EXTRACTED_MEDIA_DIR, document_id)
        os.makedirs(doc_media_dir, exist_ok=True)

        # Extract embedded images from relations
        image_map = {}
        for rel_id, rel in doc.part.related_parts.items():
            if "image" in rel.content_type:
                try:
                    ext = rel.content_type.split("/")[-1]
                    if ext == "jpeg":
                        ext = "jpg"
                    img_filename = f"image_{rel_id}.{ext}"
                    img_path = os.path.join(doc_media_dir, img_filename)
                    with open(img_path, "wb") as f:
                        f.write(rel.blob)
                    image_map[rel_id] = f"/api/media/{document_id}/{img_filename}"
                except Exception as e:
                    logger.warning(f"Failed to extract DOCX image: {e}")

        # Iterate through block elements in body order (paragraphs and tables)
        elements = []
        full_text_pieces = []
        element_idx = 0

        for block in doc.element.body:
            tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

            if tag == "p":
                # Paragraph
                p = docx.text.paragraph.Paragraph(block, doc)
                p_text = p.text.strip()
                if not p_text:
                    continue
                
                style_name = p.style.name if p.style else "Normal"
                is_bold = any(run.bold for run in p.runs if run.bold is not None)

                heading_level = 0
                if "Heading 1" in style_name or style_name == "Title":
                    heading_level = 1
                elif "Heading 2" in style_name:
                    heading_level = 2
                elif "Heading 3" in style_name:
                    heading_level = 3

                elements.append({
                    "element_order": element_idx,
                    "type": "HEADING" if heading_level > 0 else "TEXT",
                    "heading_level": heading_level,
                    "style": style_name,
                    "text": p_text,
                    "is_bold": is_bold,
                })
                full_text_pieces.append(p_text)
                element_idx += 1

            elif tag == "tbl":
                # Table
                table = docx.table.Table(block, doc)
                rows_data = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    rows_data.append(row_cells)

                html_table = self._convert_table_to_html(rows_data)
                table_text = " | ".join([" ".join(r) for r in rows_data])
                elements.append({
                    "element_order": element_idx,
                    "type": "TABLE",
                    "heading_level": 0,
                    "style": "Table",
                    "text": table_text,
                    "html": html_table,
                })
                full_text_pieces.append(table_text)
                element_idx += 1

        return {
            "elements": elements,
            "images": list(image_map.values()),
            "full_text": "\n\n".join(full_text_pieces),
        }

    def _convert_table_to_html(self, rows: List[List[str]]) -> str:
        if not rows:
            return ""
        html = ["<table class='min-w-full border border-gray-300 divide-y divide-gray-200 text-sm'>"]
        header = rows[0]
        html.append("<thead class='bg-gray-50'><tr>")
        for cell in header:
            html.append(f"<th class='px-3 py-2 text-left font-semibold text-gray-700 border-b'>{cell}</th>")
        html.append("</tr></thead>")
        html.append("<tbody class='divide-y divide-gray-200 bg-white'>")
        for row in rows[1:]:
            html.append("<tr>")
            for cell in row:
                html.append(f"<td class='px-3 py-2 border-b text-gray-800'>{cell}</td>")
            html.append("</tr>")
        html.append("</tbody></table>")
        return "".join(html)

docx_service = DOCXService()
