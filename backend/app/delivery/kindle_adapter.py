from pathlib import Path

from .adapter import DeliveryAdapter
from app.tools.send_to_kindle import send_to_kindle


class KindleAdapter(DeliveryAdapter):
    def deliver(self, epub_path: Path, metadata: dict[str, str], destination: str) -> dict[str, str | bool]:
        print(">>> Inside KindleAdapter.deliver()")
        print("Metadata:", metadata)
        kindle_email = metadata.get("kindle_email")
        sender_email = metadata.get("sender_email")
        if not kindle_email:
            return {"success": False, "error": "Kindle email is required for Kindle delivery."}

        return send_to_kindle(
            str(epub_path),
            kindle_email,
            metadata.get("title", "Unknown Title"),
            metadata.get("author", "Unknown Author"),
            smtp_sender_override=sender_email,
        )
