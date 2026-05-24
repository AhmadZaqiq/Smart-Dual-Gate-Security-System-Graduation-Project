import os
import select
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR))

from database.authentication_attempt_repository import create_authentication_attempt
from hardware import indicators
from database.access_session_repository import start_access_session
from database.system_setting_repository import get_setting_value
from hardware import devices
from core import system_status
from utils import notification_manager

class AuthenticationManager:

    def __init__(self):
        self.auth_dir = os.path.dirname(os.path.abspath(__file__))

        self.failed_attempts = 0
        self.authentication_completed = False

        self.cancel_requested = False
        self.back_cancel_enabled = False

        self.current_employee_id = None
        self.current_access_session_id = None
        self.current_auth_stage = "IDLE"

    def start(self):
        print("[AUTH] Authentication modules started", flush=True)

    def stop(self):
        self.back_cancel_enabled = False
        self.current_auth_stage = "IDLE"
        self._publish_auth_stage("IDLE")
        print("[AUTH] Authentication modules stopped", flush=True)

    def reset_session(self):
        self.failed_attempts = 0
        self.authentication_completed = False

        self.cancel_requested = False
        self.back_cancel_enabled = False

        self.current_employee_id = None
        self.current_access_session_id = None
        self.current_auth_stage = "IDLE"
        self._publish_auth_stage("IDLE")

        print("[AUTH] Authentication session reset", flush=True)

    def get_failed_attempts(self):
        return self.failed_attempts

    def get_current_employee_id(self):
        return self.current_employee_id

    def get_current_access_session_id(self):
        return self.current_access_session_id

    def get_current_auth_stage(self):
        return self.current_auth_stage

    def _publish_auth_stage(self, stage):
        self.current_auth_stage = stage

        try:
            system_status.update_status_snapshot(auth_stage=stage)
        except Exception:
            pass

        print(f"[AUTH] Current dashboard auth stage: {stage}", flush=True)

    def _publish_auth_stage_from_helper_line(self, line):
        if line.startswith("RFID_READY") or line.startswith("RFID_CARD_DETECTED"):
            self._publish_auth_stage("RFID")
            return

        if line.startswith("FINGER_READY") or line.startswith("PUT_FINGER"):
            self._publish_auth_stage("FINGERPRINT")
            return

        if line.startswith("FACE_READY") or line.startswith("FACE_CAMERA_READY") or line.startswith("FACE_LOOKING"):
            self._publish_auth_stage("FACE")
            return

        if line.startswith("BEHAVIOR_READY") or "[BEHAVIOR]" in line:
            self._publish_auth_stage("BEHAVIOR")
            return

    def is_cancel_requested(self):
        return self.cancel_requested

    def _get_int_setting(self, key, default_value):
        try:
            return int(get_setting_value(key, default_value))
        except Exception:
            return default_value

    def _get_bool_setting(self, key, default_value=True):
        try:
            return int(get_setting_value(key, 1 if default_value else 0)) == 1
        except Exception:
            return default_value

    def _load_auth_settings(self):
        return {
            "max_rfid_attempts": self._get_int_setting("MAX_RFID_ATTEMPTS", 3),
            "max_fingerprint_attempts": self._get_int_setting("MAX_FINGERPRINT_ATTEMPTS", 3),
            "max_face_attempts": self._get_int_setting("MAX_FACE_ATTEMPTS", 3),
            "max_behavior_attempts": self._get_int_setting("MAX_BEHAVIOR_ATTEMPTS", 1),
            "max_total_attempts": self._get_int_setting("MAX_AUTH_TOTAL_ATTEMPTS", 10),

            "require_rfid": self._get_bool_setting("REQUIRE_RFID", True),
            "require_fingerprint": self._get_bool_setting("REQUIRE_FINGERPRINT", True),
            "require_face": self._get_bool_setting("REQUIRE_FACE_RECOGNITION", True),
            "require_behavior": self._get_bool_setting("REQUIRE_BEHAVIOR_ANALYSIS", True),
        }

    def _run_helper(self, script_name):
        script_path = os.path.join(self.auth_dir, script_name)

        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        output_lines = []

        while True:
            if self.cancel_requested:
                print("[AUTH] Cancelling active authentication helper", flush=True)

                process.kill()
                process.wait()

                return False, output_lines

            ready, _, _ = select.select([process.stdout], [], [], 0.1)

            if ready:
                line = process.stdout.readline()

                if line:
                    clean_line = line.strip()
                    output_lines.append(clean_line)
                    print(f"[AUTH] {clean_line}", flush=True)
                    self._publish_auth_stage_from_helper_line(clean_line)

            if process.poll() is not None:
                remaining_output = process.stdout.read()

                if remaining_output:
                    for line in remaining_output.splitlines():
                        clean_line = line.strip()
                        output_lines.append(clean_line)
                        print(f"[AUTH] {clean_line}", flush=True)
                        self._publish_auth_stage_from_helper_line(clean_line)

                break

        return process.returncode == 0, output_lines

    def _get_value_from_output(self, output_lines, prefix):
        for line in output_lines:
            if line.startswith(prefix):
                return line.split(":", 1)

        return None

    def _send_behavior_email_alert(self, message, severity="MEDIUM"):
        print("[ALERT] Behavior alert redirected to Email Alert channel", flush=True)
        notification_manager.send_email_security_alert(
            message=message,
            alert_title="Authentication Behavior Alert",
            severity=severity,
            include_snapshots=True
        )

    def _send_whatsapp_alert_stub(self, message, severity="MEDIUM"):
        self._send_behavior_email_alert(message, severity)

    def _log_failed_attempt(self, rfid_status=None, fingerprint_status=None,
                            face_status=None, behavior_status=None,
                            failure_reason=None):
        create_authentication_attempt(
            access_session_id=self.current_access_session_id,
            employee_id=self.current_employee_id,

            rfid_status=rfid_status,
            fingerprint_status=fingerprint_status,
            face_status=face_status,
            behavior_status=behavior_status,

            final_result="ACCESS_DENIED",
            failure_reason=failure_reason
        )

    def _is_total_attempts_exceeded(self, settings):
        return self.failed_attempts >= settings["max_total_attempts"]

    def enable_back_cancel_after_failed_attempt(self):
        if self.back_cancel_enabled:
            return

        self.back_cancel_enabled = True

        print("[AUTH] AuthCancelButton enabled for cancel", flush=True)

        def watch_back_button():
            while self.back_cancel_enabled and not self.cancel_requested:
                if devices.is_auth_cancel_button_pressed():
                    self.cancel_requested = True
                    print("[AUTH] AUTH_CANCEL_REQUESTED", flush=True)
                    break

                time.sleep(0.05)

        threading.Thread(target=watch_back_button, daemon=True).start()

    def process_authentication(self):
        if self.authentication_completed:
            return False

        settings = self._load_auth_settings()

        print("[AUTH] Starting isolated authentication flow", flush=True)
        print(f"[AUTH] Loaded settings: {settings}", flush=True)
        self._publish_auth_stage("STARTING")

        rfid_status = "SKIPPED"
        fingerprint_status = "SKIPPED"
        face_status = "SKIPPED"
        behavior_status = "SKIPPED"

        if settings["require_rfid"]:
            self._publish_auth_stage("RFID")
            print("[AUTH] Step 1: RFID", flush=True)

            rfid_ok = False

            for attempt in range(1, settings["max_rfid_attempts"] + 1):
                print(
                    f"[AUTH] RFID attempt {attempt}/{settings['max_rfid_attempts']}",
                    flush=True
                )

                helper_ok, rfid_output = self._run_helper("auth_rfid_only.py")

                if helper_ok:
                    rfid_data = self._get_value_from_output(rfid_output, "RFID_OK:")

                    if rfid_data and len(rfid_data) >= 2:
                        rfid_token = rfid_data[1]

                        print(f"[AUTH] RFID shared token accepted: {rfid_token}", flush=True)

                        rfid_status = "RFID_OK"
                        rfid_ok = True
                        indicators.beep_success()
                        break

                self.failed_attempts += 1

                if self.cancel_requested:
                    return False

                indicators.beep_error()
                print("[AUTH] RFID attempt failed", flush=True)

                self.enable_back_cancel_after_failed_attempt()

                if self.cancel_requested:
                    return False

                if self._is_total_attempts_exceeded(settings):
                    break

            if not rfid_ok:
                self._publish_auth_stage("FAILED")
                self._log_failed_attempt(
                    rfid_status="RFID_FAILED",
                    fingerprint_status=fingerprint_status,
                    face_status=face_status,
                    behavior_status=behavior_status,
                    failure_reason="RFID authentication failed"
                )
                return False

        else:
            print("[AUTH] RFID step skipped by system settings", flush=True)

        if settings["require_fingerprint"]:
            self._publish_auth_stage("FINGERPRINT")
            print("[AUTH] Step 2: Fingerprint", flush=True)

            fingerprint_ok = False

            for attempt in range(1, settings["max_fingerprint_attempts"] + 1):
                print(
                    f"[AUTH] Fingerprint attempt {attempt}/{settings['max_fingerprint_attempts']}",
                    flush=True
                )

                helper_ok, finger_output = self._run_helper("auth_fingerprint_only.py")

                if helper_ok:
                    finger_data = self._get_value_from_output(finger_output, "FINGER_OK:")

                    if finger_data and len(finger_data) >= 2:
                        finger_values = finger_data[1].split(":")

                        finger_employee_id = int(finger_values[0])
                        finger_position = finger_values[1] if len(finger_values) > 1 else "UNKNOWN"
                        finger_accuracy = finger_values[2] if len(finger_values) > 2 else "UNKNOWN"

                        self.current_employee_id = finger_employee_id

                        fingerprint_status = "FINGER_OK"
                        fingerprint_ok = True
                        indicators.beep_success()

                        print(
                            f"[AUTH] Fingerprint employee identified: "
                            f"{finger_employee_id}, Position: {finger_position}, "
                            f"Accuracy: {finger_accuracy}",
                            flush=True
                        )
                        break

                if self.cancel_requested:
                    return False

                self.failed_attempts += 1

                indicators.beep_error()
                print("[AUTH] Fingerprint attempt failed", flush=True)

                self.enable_back_cancel_after_failed_attempt()

                if self.cancel_requested:
                    return False

                if self._is_total_attempts_exceeded(settings):
                    break

            if not fingerprint_ok:
                self._publish_auth_stage("FAILED")
                self._log_failed_attempt(
                    rfid_status=rfid_status,
                    fingerprint_status="FINGER_FAILED",
                    face_status=face_status,
                    behavior_status=behavior_status,
                    failure_reason="Fingerprint authentication failed"
                )
                return False

        else:
            print("[AUTH] Fingerprint step skipped by system settings", flush=True)
            self.current_employee_id = self._get_int_setting("DEFAULT_EMPLOYEE_ID", 1)

        if settings["require_face"]:
            self._publish_auth_stage("FACE")
            print("[AUTH] Step 3: Face Recognition", flush=True)

            face_ok = False

            for attempt in range(1, settings["max_face_attempts"] + 1):
                print(
                    f"[AUTH] Face recognition attempt {attempt}/{settings['max_face_attempts']}",
                    flush=True
                )

                os.environ["FACE_EMPLOYEE_ID"] = str(self.current_employee_id)

                helper_ok, face_output = self._run_helper("auth_face_only.py")

                if helper_ok:
                    face_status = "FACE_OK"
                    face_ok = True
                    indicators.beep_success()

                    print("[AUTH] Face recognition stage finished", flush=True)
                    break

                if self.cancel_requested:
                    return False

                self.failed_attempts += 1

                indicators.beep_error()
                print("[AUTH] Face recognition attempt failed", flush=True)

                self.enable_back_cancel_after_failed_attempt()

                if self.cancel_requested:
                    return False

                if self._is_total_attempts_exceeded(settings):
                    break

            if not face_ok:
                self._publish_auth_stage("FAILED")
                self._log_failed_attempt(
                    rfid_status=rfid_status,
                    fingerprint_status=fingerprint_status,
                    face_status="FACE_FAILED",
                    behavior_status=behavior_status,
                    failure_reason="Face recognition failed"
                )
                return False

        else:
            print("[AUTH] Face recognition step skipped by system settings", flush=True)

        if settings["require_behavior"]:
            print("[AUTH] Step 4: Dlib Behavior Check", flush=True)

            behavior_ok = False

            for attempt in range(1, settings["max_behavior_attempts"] + 1):
                print(
                    f"[AUTH] Behavior attempt {attempt}/{settings['max_behavior_attempts']}",
                    flush=True
                )

                helper_ok, behavior_output = self._run_helper("auth_behavior_only.py")

                if self.cancel_requested:
                    return False

                if helper_ok:
                    if "BEHAVIOR_NORMAL" in behavior_output:
                        behavior_status = "BEHAVIOR_NORMAL"
                        behavior_ok = True

                        print("[AUTH] Behavior check normal", flush=True)
                        break

                    if "BEHAVIOR_MEDIUM" in behavior_output:
                        behavior_status = "BEHAVIOR_MEDIUM"
                        behavior_ok = True

                        print("[AUTH] Behavior check medium warning", flush=True)

                        self._send_behavior_email_alert(
                            "Medium suspicious behavior detected during authentication",
                            severity="MEDIUM"
                        )
                        break

                self.failed_attempts += 1
                behavior_status = "BEHAVIOR_DANGER"

                print("[AUTH] Behavior check danger detected", flush=True)

                self._send_behavior_email_alert(
                    "Danger behavior detected during authentication",
                    severity="HIGH"
                )

                self.enable_back_cancel_after_failed_attempt()

                if self.cancel_requested:
                    return False

                if self._is_total_attempts_exceeded(settings):
                    break

            if not behavior_ok:
                self._publish_auth_stage("FAILED")
                self._log_failed_attempt(
                    rfid_status=rfid_status,
                    fingerprint_status=fingerprint_status,
                    face_status=face_status,
                    behavior_status=behavior_status,
                    failure_reason="Danger behavior detected"
                )
                return False

        else:
            print("[AUTH] Behavior analysis step skipped by system settings", flush=True)

        self.current_access_session_id = start_access_session(
            employee_id=self.current_employee_id
        )

        create_authentication_attempt(
            access_session_id=self.current_access_session_id,
            employee_id=self.current_employee_id,

            rfid_status=rfid_status,
            fingerprint_status=fingerprint_status,
            face_status=face_status,
            behavior_status=behavior_status,

            final_result="ACCESS_GRANTED",
            failure_reason=None
        )

        print(f"[AUTH] Access session started: {self.current_access_session_id}", flush=True)
        print(f"[AUTH] Authentication success for EmployeeID: {self.current_employee_id}", flush=True)

        self._publish_auth_stage("ACCESS_GRANTED")
        self.authentication_completed = True
        return True


_auth_manager = AuthenticationManager()


def start_authentication_modules():
    _auth_manager.start()


def stop_authentication_modules():
    _auth_manager.stop()


def reset_authentication_session():
    _auth_manager.reset_session()


def process_authentication():
    return _auth_manager.process_authentication()


def get_failed_attempts_count():
    return _auth_manager.get_failed_attempts()


def get_current_employee_id():
    return _auth_manager.get_current_employee_id()


def get_current_access_session_id():
    return _auth_manager.get_current_access_session_id()


def is_cancel_requested():
    return _auth_manager.is_cancel_requested()


def get_current_auth_stage():
    return _auth_manager.get_current_auth_stage()
