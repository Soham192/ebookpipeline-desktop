import mimetypes
import os
import smtplib
import ssl
import socket
import subprocess
from email.message import EmailMessage
from pathlib import Path


def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def verify_smtp_credentials() -> dict[str, str | bool]:
    smtp_host = os.environ.get("SMTP_HOST") or "localhost"
    smtp_port_value = os.environ.get("SMTP_PORT")
    if smtp_port_value:
        smtp_port = int(smtp_port_value)
    elif smtp_host == "localhost" and port_open("localhost", 1025):
        smtp_port = 1025
    else:
        smtp_port = 25

    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_use_tls = (
        os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
        if os.environ.get("SMTP_USE_TLS") is not None
        else (False if smtp_host in ("localhost", "127.0.0.1") else True)
    )
    smtp_use_ssl = (
        os.environ.get("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
        if os.environ.get("SMTP_USE_SSL") is not None
        else smtp_port == 465
    )

    if not smtp_user or not smtp_password:
        return {
            "success": False,
            "error": "SMTP_USER and SMTP_PASSWORD must be set to verify credentials.",
        }

    try:
        context = ssl.create_default_context()
        if smtp_use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=30) as server:
                server.login(smtp_user, smtp_password)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                if smtp_use_tls:
                    server.starttls(context=context)
                server.login(smtp_user, smtp_password)
        return {"success": True, "message": "SMTP credentials are valid."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def send_to_kindle(output_path: str, kindle_email: str, title: str, author: str, smtp_sender_override: str | None = None) -> dict[str, str | bool]:
    """Send the converted ebook to the user's Kindle email.

    Returns a structured dict: { sent: bool, recipient: str, error?: str }
    """
    print(">>> Inside send_to_kindle()")

    output_path = Path(output_path)

    def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
        import socket

        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    smtp_host = os.environ.get("SMTP_HOST") or "localhost"
    smtp_port_value = os.environ.get("SMTP_PORT")
    if smtp_port_value:
        smtp_port = int(smtp_port_value)
    elif smtp_host == "localhost" and port_open("localhost", 1025):
        smtp_port = 1025
    else:
        smtp_port = 25

    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_sender = smtp_sender_override or os.environ.get("SMTP_SENDER") or smtp_user
    smtp_use_tls = (
        os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
        if os.environ.get("SMTP_USE_TLS") is not None
        else (False if smtp_host in ("localhost", "127.0.0.1") else True)
    )
    smtp_use_ssl = (
        os.environ.get("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
        if os.environ.get("SMTP_USE_SSL") is not None
        else smtp_port == 465
    )

    if not smtp_sender:
        if smtp_host == "localhost" and smtp_port == 1025:
            smtp_sender = "sender@example.com"
        else:
            return {"sent": False, "error": "No sender specified. Provide SMTP_SENDER environment variable or a Sender Email in the upload form."}

    msg = EmailMessage()
    msg["From"] = smtp_sender
    msg["To"] = kindle_email
    msg["Subject"] = f"Your Kindle ebook: {title}"
    msg.set_content(
        (
            f"Your converted ebook is attached.\n\n"
            f"If this sender is not approved by Amazon, add {smtp_sender} to your Kindle "
            "Approved Personal Document E-mail list before resending."
        )
    )

    guessed_type, _ = mimetypes.guess_type(output_path.name)
    maintype, subtype = (guessed_type or "application/octet-stream").split("/", 1)
    with output_path.open("rb") as f:
        msg.add_attachment(
            f.read(),
            maintype=maintype,
            subtype=subtype,
            filename=output_path.name,
        )

    # Try SMTP send with explicit envelope sender
    smtp_error = None
    try:
        context = ssl.create_default_context()
        if smtp_use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=30) as server:
                if smtp_user and smtp_password:
                    try:
                        server.login(smtp_user, smtp_password)
                    except Exception as exc:
                        raise RuntimeError(f"SMTP authentication failed: {exc}") from exc
                server.sendmail(smtp_sender, [kindle_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                if smtp_use_tls:
                    try:
                        server.starttls(context=context)
                    except Exception:
                        pass
                if smtp_user and smtp_password:
                    try:
                        server.login(smtp_user, smtp_password)
                    except Exception as exc:
                        raise RuntimeError(f"SMTP authentication failed: {exc}") from exc
                server.sendmail(smtp_sender, [kindle_email], msg.as_string())
        return {"sent": True, "recipient": kindle_email}
    except ConnectionRefusedError as exc:
        smtp_error = str(exc)
        if smtp_host == "localhost" and smtp_port == 25 and port_open("localhost", 1025):
            smtp_host = "localhost"
            smtp_port = 1025
            try:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                    if smtp_use_tls:
                        try:
                            server.starttls(context=context)
                        except Exception:
                            pass
                    if smtp_user and smtp_password:
                        try:
                            server.login(smtp_user, smtp_password)
                        except Exception:
                            pass
                    server.sendmail(smtp_sender, [kindle_email], msg.as_string())
                return {"sent": True, "recipient": kindle_email}
            except Exception as exc2:
                smtp_error = str(exc2)
    except Exception as exc:
        smtp_error = str(exc)

    # If SMTP failed, try local sendmail binary
    sendmail_paths = ["/usr/sbin/sendmail", "/usr/lib/sendmail", "/usr/sbin/exim", "/usr/sbin/postfix"]
    sendmail_cmd = None
    for path in sendmail_paths:
        if Path(path).exists():
            sendmail_cmd = path
            break

    if sendmail_cmd:
        try:
            p = subprocess.Popen([sendmail_cmd, "-t", "-oi"], stdin=subprocess.PIPE)
            p.communicate(input=msg.as_bytes())
            if p.returncode == 0:
                return {"sent": True, "recipient": kindle_email}
            else:
                return {"sent": False, "error": f"sendmail failed with code {p.returncode}: {smtp_error}"}
        except Exception as exc:
            return {"sent": False, "error": f"sendmail fallback failed: {exc}; smtp_error: {smtp_error}"}

    return {"sent": False, "error": f"SMTP send failed: {smtp_error}"}
