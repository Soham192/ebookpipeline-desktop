from pathlib import Path

from .adapter import DeliveryAdapter


class DownloadAdapter(DeliveryAdapter):
    def deliver(self, epub_path: Path, metadata: dict[str, str], destination: str) -> dict[str, str | bool]:
        return {
            "success": True,
            "destination": "download",
            "message": "EPUB is ready for download.",
            "file_path": str(epub_path),
            "metadata": metadata,
        }
