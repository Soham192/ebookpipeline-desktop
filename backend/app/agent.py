from pathlib import Path
import shutil
from typing import TypedDict

from app.tools.analyze_pdf import PdfAnalysis, analyze_pdf
from app.tools.run_ocr import run_ocr
from app.tools.extract_metadata import extract_metadata
from app.tools.convert_document import convert_document


class ProcessResult(TypedDict):
    output_path: str
    format: str
    title: str
    author: str
    requires_ocr: bool
    ocr_error: str | None


class Agent:
    async def process_pdf(
        self,
        pdf_path: Path | str,
        metadata: dict[str, str | None],
        output_format: str = "azw3",
        output_name: str | None = None,
    ) -> ProcessResult:
        pdf_path = Path(pdf_path)
        analysis = analyze_pdf(pdf_path)

        ocr_error = None
        if analysis["requires_ocr"]:
            ocr_pdf_path = pdf_path.parent / f"{pdf_path.stem}_ocr.pdf"
            try:
                run_ocr(pdf_path, ocr_pdf_path)
                pdf_path = ocr_pdf_path
            except RuntimeError as exc:
                ocr_error = str(exc)

        extracted = extract_metadata(pdf_path)
        title = metadata.get("title") or extracted.get("title") or "Unknown Title"
        author = metadata.get("author") or extracted.get("author") or "Unknown Author"

        output_name = output_name or pdf_path.stem
        output_path = pdf_path.parent.parent / "outputs" / f"{output_name}.{output_format}"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # If the user requested PDF, skip conversion and just copy the original PDF.
        if output_format == "pdf":
            shutil.copy2(pdf_path, output_path)
            return {
                "output_path": str(output_path),
                "format": "pdf",
                "title": title,
                "author": author,
                "requires_ocr": analysis["requires_ocr"],
                "ocr_error": ocr_error,
            }

        convert_document(
            pdf_path,
            output_path,
            title=title,
            author=author,
            output_format=output_format,
        )

        return {
            "output_path": str(output_path),
            "format": output_format,
            "title": title,
            "author": author,
            "requires_ocr": analysis["requires_ocr"],
            "ocr_error": ocr_error,
        }
