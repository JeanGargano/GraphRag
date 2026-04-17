import logging
from typing import Optional

from PyPDF2 import PdfReader
from docx import Document as DocxDocument

from Service.IExtraction_Strategy import IExtractionStrategy

logger = logging.getLogger(__name__)


class PDFExtractionStrategy(IExtractionStrategy):

    def extract_content(self, file_path: str) -> Optional[str]:
        try:
            reader = PdfReader(file_path)
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            if not pages_text:
                logger.warning("PDF sin texto extraíble: %s", file_path)
                return None
            return "\n".join(pages_text).strip()
        except Exception as e:
            logger.error("Error extrayendo PDF '%s': %s", file_path, e)
            return None


class DocxExtractionStrategy(IExtractionStrategy):

    def extract_content(self, file_path: str) -> Optional[str]:
        try:
            doc = DocxDocument(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            if not paragraphs:
                logger.warning("DOCX sin texto extraíble: %s", file_path)
                return None
            return "\n".join(paragraphs).strip()
        except Exception as e:
            logger.error("Error extrayendo DOCX '%s': %s", file_path, e)
            return None


class TxtExtractionStrategy(IExtractionStrategy):

    def extract_content(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if not text:
                logger.warning("TXT vacío: %s", file_path)
                return None
            return text
        except Exception as e:
            logger.error("Error extrayendo TXT '%s': %s", file_path, e)
            return None