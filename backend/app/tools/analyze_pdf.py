from pathlib import Path
from typing import TypedDict

import fitz


class PdfAnalysis(TypedDict):
    pages: int
    scanned_pages: int
    requires_ocr: bool


def analyze_pdf(pdf_path: str | Path) -> PdfAnalysis:
    pdf_path = Path(pdf_path)
    doc = fitz.open(str(pdf_path))
    try:
        scanned_pages = 0
        for page in doc:
            text = page.get_text().strip()
            if len(text) < 50:
                scanned_pages += 1
        return {
            "pages": doc.page_count,
            "scanned_pages": scanned_pages,
            "requires_ocr": scanned_pages > 0,
        }
    finally:
        doc.close()
