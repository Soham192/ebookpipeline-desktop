from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import shutil
import json

from dotenv import load_dotenv
from app.agent import Agent
from app.delivery.download_adapter import DownloadAdapter
from app.delivery.kindle_adapter import KindleAdapter
from app.tools.send_to_kindle import send_to_kindle, verify_smtp_credentials

load_dotenv()

app = FastAPI(title="Universal E-Reader Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PENDING_DIR = Path(__file__).resolve().parent.parent / "pending_deliveries"
PENDING_DIR.mkdir(parents=True, exist_ok=True)

agent = Agent()
DELIVERY_ADAPTERS = {
    "download": DownloadAdapter(),
    "kindle": KindleAdapter(),
}

@app.get("/smtp_test")
def smtp_test():
    result = verify_smtp_credentials()
    if result.get("success"):
        return result
    raise HTTPException(status_code=400, detail=result.get("error", "SMTP validation failed"))

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    author: str | None = Form(None),
    kindle_email: str | None = Form(None),
    sender_email: str | None = Form(None),
    destination: str | None = Form("download"),
):
    allowed_destinations = {"download", "kindle"}
    destination = (destination or "download").lower()
    if destination not in allowed_destinations:
        raise HTTPException(status_code=400, detail="Unsupported destination")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    file_id = uuid4().hex
    saved_path = UPLOAD_DIR / f"{file_id}.pdf"
    with saved_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    metadata = {
        "title": title,
        "author": author,
        "kindle_email": kindle_email,
        "sender_email": sender_email,
    }
    try:
        result = await agent.process_pdf(
            str(saved_path),
            metadata,
            output_format="epub",
            output_name=file_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    delivery_adapter = DELIVERY_ADAPTERS[destination]
    delivery_result = delivery_adapter.deliver(
        Path(result["output_path"]),
        metadata,
        destination,
    )

    if destination == "kindle" and not delivery_result.get("sent"):
        pending = {
            "task_id": file_id,
            "output_path": result["output_path"],
            "kindle_email": kindle_email,
            "sender_email": sender_email,
            "title": result["title"],
            "author": result["author"],
            "error": delivery_result.get("error"),
        }
        pending_file = PENDING_DIR / f"{file_id}.json"
        with pending_file.open("w", encoding="utf-8") as pf:
            json.dump(pending, pf)

    return {
        "status": "ok",
        "task_id": file_id,
        "destination": destination,
        "download_url": f"http://localhost:8000/download/{file_id}/{result['format']}",
        "output": result,
        "delivery": delivery_result,
        "delivery_queued": bool(destination == "kindle" and not delivery_result.get("sent")),
    }


@app.post("/retry_delivery/{task_id}")
def retry_delivery(task_id: str):
    pending_file = PENDING_DIR / f"{task_id}.json"
    if not pending_file.exists():
        raise HTTPException(status_code=404, detail="No pending delivery for this task")

    with pending_file.open("r", encoding="utf-8") as pf:
        pending = json.load(pf)

    try:
        result = send_to_kindle(
            pending["output_path"],
            pending["kindle_email"],
            pending.get("title", ""),
            pending.get("author", ""),
            smtp_sender_override=pending.get("sender_email"),
        )
    except RuntimeError as exc:
        return {"sent": False, "error": str(exc)}

    if result.get("sent"):
        try:
            pending_file.unlink()
        except Exception:
            pass

    return result

@app.get("/download/{task_id}/{output_format}")
def download_output(task_id: str, output_format: str):
    output_path = OUTPUT_DIR / f"{task_id}.{output_format}"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output not found")
    return FileResponse(output_path, filename=output_path.name, media_type="application/octet-stream")
