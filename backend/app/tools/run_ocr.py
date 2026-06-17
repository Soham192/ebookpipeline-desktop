import subprocess
from pathlib import Path


def run_ocr(input_pdf: str, output_pdf: str) -> None:
    input_pdf = Path(input_pdf)
    output_pdf = Path(output_pdf)

    command = [
        "ocrmypdf",
        "--skip-text",
        "--output-type",
        "pdf",
        str(input_pdf),
        str(output_pdf),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "OCR tool not found. Please install ocrmypdf and tesseract."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else str(exc)
        raise RuntimeError(
            "OCR processing failed. This can happen if the PDF is malformed or Ghostscript cannot render it. "
            f"Command output: {stderr}"
        ) from exc
