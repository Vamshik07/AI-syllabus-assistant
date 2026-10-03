import logging
import os
import shutil

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.tesseract_cmd = shutil.which("tesseract")
        if not self.tesseract_cmd:
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"/usr/bin/tesseract",
                r"/usr/local/bin/tesseract",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    self.tesseract_cmd = path
                    break

        if self.tesseract_cmd:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
                self.available = True
                logger.info(f"Tesseract OCR initialized at {self.tesseract_cmd}")
            except Exception as e:
                logger.warning(f"Failed to configure pytesseract: {e}")
                self.available = False
        else:
            self.available = False
            logger.info("Tesseract OCR binary not found. Scanned-only PDFs will use raw text extraction.")

    def is_available(self) -> bool:
        return self.available

    def ocr_image(self, image) -> str:
        """Performs OCR on a PIL image if Tesseract is available."""
        if not self.available:
            return ""
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""

ocr_service = OCRService()
