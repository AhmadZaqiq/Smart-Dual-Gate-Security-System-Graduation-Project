import os
import sqlite3
import smtplib
import socket
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "mantrap.db"

FACE_CAMERA_PATH = "/dev/mantrap-facecam"
INNER_CAMERA_PATH = "/dev/mantrap-innercam"

SNAPSHOT_DIR = PROJECT_ROOT / "runtime" / "email_alert_snapshots"


def _get_env_value(key, default_value=""):
    value = os.environ.get(key)

    if value:
        return value.strip()

    env_path = PROJECT_ROOT / ".env"

    if not env_path.exists():
        return default_value

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            clean_line = line.strip()

            if not clean_line or clean_line.startswith("#"):
                continue

            if "=" not in clean_line:
                continue

            env_key, env_value = clean_line.split("=", 1)

            if env_key.strip() == key:
                return env_value.strip().strip('"').strip("'")

    except Exception:
        return default_value

    return default_value


def _get_dashboard_url():
    return _get_env_value(
        "DASHBOARD_PUBLIC_URL",
        "http://192.168.1.28:8000"
    )


def _get_active_admin_emails():
    admin_emails = []

    if not DATABASE_PATH.exists():
        print(f"[ALERT] Database not found: {DATABASE_PATH}", flush=True)
        return admin_emails

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT UserName, Email
            FROM AdminUser
            WHERE IsActive = 1
              AND IsDeleted = 0
              AND Email IS NOT NULL
              AND TRIM(Email) != ''
            ORDER BY AdminUserID
            """
        )

        for row in cursor.fetchall():
            username = row["UserName"]
            email = row["Email"].strip()

            if email.endswith("@mantrap.local"):
                print(
                    f"[ALERT] Skipping local admin email for {username}: {email}",
                    flush=True
                )
                continue

            admin_emails.append(email)

    except Exception as error:
        print(f"[ALERT] Failed to load admin emails: {error}", flush=True)

    finally:
        connection.close()

    return admin_emails


def _capture_camera_snapshot(camera_path, output_path, label):
    try:
        if not Path(camera_path).exists():
            print(f"[ALERT] {label} path not found: {camera_path}", flush=True)
            return None

        for attempt in range(1, 4):
            print(f"[ALERT] Opening {label} snapshot attempt {attempt}/3", flush=True)

            camera = cv2.VideoCapture(camera_path, cv2.CAP_V4L2)
            camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_FPS, 10)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not camera.isOpened():
                print(f"[ALERT] Failed to open {label} on attempt {attempt}", flush=True)
                camera.release()
                time.sleep(0.5)
                continue

            frame = None
            success = False

            # Warm up the camera before saving the final frame.
            for _ in range(8):
                camera.read()
                time.sleep(0.05)

            for _ in range(30):
                success, frame = camera.read()

                if success and frame is not None:
                    break

                time.sleep(0.1)

            camera.release()

            if success and frame is not None:
                cv2.imwrite(str(output_path), frame)
                print(f"[ALERT] {label} snapshot saved: {output_path}", flush=True)
                return output_path

            print(f"[ALERT] Failed to capture {label} frame on attempt {attempt}", flush=True)
            time.sleep(0.5)

        print(f"[ALERT] {label} snapshot unavailable after retries", flush=True)
        return None

    except Exception as error:
        print(f"[ALERT] {label} snapshot error: {error}", flush=True)
        return None

def _capture_yolo_inner_snapshot(output_path):
    try:
        from ai import yolo_room_monitor

        if yolo_room_monitor.save_latest_frame_snapshot(output_path):
            print(f"[ALERT] InnerCam YOLO snapshot saved: {output_path}", flush=True)
            return output_path

        print("[ALERT] No YOLO latest frame available for InnerCam snapshot", flush=True)
        return None

    except Exception as error:
        print(f"[ALERT] YOLO InnerCam snapshot error: {error}", flush=True)
        return None


def _capture_alert_snapshots():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    attachments = []

    face_snapshot = _capture_camera_snapshot(
        FACE_CAMERA_PATH,
        SNAPSHOT_DIR / f"facecam_{timestamp}.jpg",
        "FaceCam"
    )

    if face_snapshot:
        attachments.append(face_snapshot)

    inner_snapshot = _capture_yolo_inner_snapshot(
        SNAPSHOT_DIR / f"innercam_yolo_{timestamp}.jpg"
    )

    if inner_snapshot:
        attachments.append(inner_snapshot)
    else:
        # Safe fallback only when YOLO latest frame is not available.
        # If YOLO owns the camera, this may fail without harming the alert.
        direct_inner_snapshot = _capture_camera_snapshot(
            INNER_CAMERA_PATH,
            SNAPSHOT_DIR / f"innercam_direct_{timestamp}.jpg",
            "InnerCam"
        )

        if direct_inner_snapshot:
            attachments.append(direct_inner_snapshot)

    return attachments


def _build_email_body(alert_title, message, severity):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hostname = socket.gethostname()
    dashboard_url = _get_dashboard_url()

    live_monitor_url = f"{dashboard_url}/live/"
    dashboard_home_url = f"{dashboard_url}/dashboard/"

    return f"""
Smart Dual-Gate Security System Alert

Alert Title:
{alert_title}

Severity:
{severity}

Message:
{message}

System Host:
{hostname}

Timestamp:
{current_time}

Local Dashboard Link:
{dashboard_home_url}

Local Live Monitor Link:
{live_monitor_url}

Important Network Note:
These links are local Raspberry Pi network links. They work only when the phone or laptop is connected to the same Wi-Fi/network as the Raspberry Pi.

3D Mantrap Visual:
Open the dashboard overview page from the same local network to view the live 3D mantrap model.

Attached Evidence:
- FaceCam snapshot if available
- InnerCam / YOLO snapshot if available

This is an automated security notification generated by the Smart Dual-Gate Security System.
"""


def send_email_security_alert(message, alert_title="Security Alert", severity="HIGH", include_snapshots=True):
    sender_email = _get_env_value("ALERT_EMAIL_ADDRESS")
    sender_password = _get_env_value("ALERT_EMAIL_APP_PASSWORD")

    if not sender_email or not sender_password:
        print("[ALERT] Email alert is not configured", flush=True)
        print("[ALERT] Add ALERT_EMAIL_ADDRESS and ALERT_EMAIL_APP_PASSWORD to .env", flush=True)
        print(f"[ALERT] Message: {message}", flush=True)
        return False

    recipients = _get_active_admin_emails()

    if not recipients:
        print("[ALERT] No active admin emails found", flush=True)
        print(f"[ALERT] Message: {message}", flush=True)
        return False

    email_message = EmailMessage()
    email_message["From"] = sender_email
    email_message["To"] = ", ".join(recipients)
    email_message["Subject"] = f"[MANTRAP ALERT] {alert_title}"

    email_message.set_content(
        _build_email_body(
            alert_title=alert_title,
            message=message,
            severity=severity
        )
    )

    attachments = []

    if include_snapshots:
        attachments = _capture_alert_snapshots()

    for attachment_path in attachments:
        try:
            with open(attachment_path, "rb") as file:
                image_data = file.read()

            email_message.add_attachment(
                image_data,
                maintype="image",
                subtype="jpeg",
                filename=attachment_path.name
            )

        except Exception as error:
            print(f"[ALERT] Failed to attach {attachment_path}: {error}", flush=True)

    try:
        print(f"[ALERT] Sending email alert to admins: {recipients}", flush=True)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(email_message)

        print("[ALERT] Email security alert sent successfully", flush=True)
        return True

    except Exception as error:
        print(f"[ALERT] Failed to send email alert: {error}", flush=True)
        print(f"[ALERT] Message: {message}", flush=True)
        return False


def send_security_alert(message, alert_title="Security Alert", severity="HIGH", include_snapshots=True):
    return send_email_security_alert(
        message=message,
        alert_title=alert_title,
        severity=severity,
        include_snapshots=include_snapshots
    )


def send_whatsapp_security_alert(message):
    print("[ALERT] WhatsApp alert channel replaced by Email Alert", flush=True)

    return send_security_alert(
        message=message,
        alert_title="Security Lockdown Alert",
        severity="HIGH",
        include_snapshots=True
    )
