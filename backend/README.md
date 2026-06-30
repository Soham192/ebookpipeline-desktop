# Universal E-Reader Agent Backend

## Setup

1. Install Python 3.11+.
2. Install dependencies:

```bash
python -m pip install poetry
poetry install
```

3. Run the FastAPI server:

```bash
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If Poetry is not available, start directly from the project virtual environment:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

The backend now uses a modular delivery adapter architecture. The upload process converts uploaded PDFs into EPUB by default, then passes the EPUB to a destination adapter:

- `download` → returns a downloadable EPUB
- `kindle` → sends the EPUB to a Kindle email address via SMTP

This makes it easy to add new delivery destinations as adapters without changing the core agent logic.

## API Contract

### `POST /upload`

Uploads a PDF and selects a delivery destination.

Form fields:

- `file` (file, required): PDF document
- `title` (string, optional): override title metadata
- `author` (string, optional): override author metadata
- `destination` (string, optional): `download` or `kindle` (default: `download`)
- `kindle_email` (string, optional): required when `destination=kindle`
- `sender_email` (string, optional): optional SMTP sender override

Response:

- `status`: `ok`
- `task_id`: generated task identifier
- `destination`: selected delivery destination
- `download_url`: URL for the converted EPUB download
- `output`: processing result metadata
- `delivery`: delivery adapter result
- `delivery_queued`: true when Kindle delivery failed and is queued for retry

### `GET /download/{task_id}/{output_format}`

Downloads the converted file from the workspace output directory.

- `task_id`: task identifier
- `output_format`: currently `epub`

### `POST /retry_delivery/{task_id}`

Retries Kindle delivery for a previously failed delivery.

- `task_id`: task identifier for a queued retry

## Requirements

- `ocrmypdf`
- `ebook-convert` (Calibre)
- `tesseract`

## Local SMTP testing with MailHog

Run MailHog and set environment variables before starting the backend:

```bash
docker run -d --name mailhog -p 1025:1025 -p 8025:8025 mailhog/mailhog
export SMTP_HOST=localhost
export SMTP_PORT=1025
export SMTP_SENDER=sender@example.com
export SMTP_USE_TLS=false
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8025 to verify incoming messages.

## Real SMTP relay configuration

To send directly to Kindle via a real SMTP relay, provide your relay credentials and approved sender in a `.env` file or environment variables.

Create `backend/.env` with:

```ini
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_SENDER=your-approved-sender@example.com
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

For SMTPS on port `465`, use:

```ini
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_SENDER=your-approved-sender@example.com
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

Then start the backend from the `backend` folder:

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Important:

- `SMTP_SENDER` must match an approved address in Amazon's "Approved Personal Document E-mail" list.
- `kindle_email` must be your actual Kindle document address (for example `yourname@kindle.com`).
- If the relay requires TLS, keep `SMTP_USE_TLS=true`.
