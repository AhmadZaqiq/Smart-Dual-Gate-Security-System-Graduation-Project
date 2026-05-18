import subprocess
import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "database"))

from employee_repository import (
    log_authentication_attempt,
    start_access_session
)


class AuthenticationManager:
    def __init__(self):
        self.auth_dir = os.path.dirname(os.path.abspath(__file__))
        self.failed_attempts = 0
        self.authentication_completed = False
        self.current_employee_id = None
        self.current_access_session_id = None

    def start(self):
        print("[AUTH] Authentication modules started")

    def stop(self):
        print("[AUTH] Authentication modules stopped")

    def reset_session(self):
        self.failed_attempts = 0
        self.authentication_completed = False
        self.current_employee_id = None
        self.current_access_session_id = None
        print("[AUTH] Authentication session reset")

    def get_failed_attempts(self):
        return self.failed_attempts

    def get_current_employee_id(self):
        return self.current_employee_id

    def get_current_access_session_id(self):
        return self.current_access_session_id

    def _run_helper(self, script_name):
        script_path = os.path.join(self.auth_dir, script_name)

        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output_lines = []

        for line in process.stdout:
            clean_line = line.strip()
            output_lines.append(clean_line)
            print(f"[AUTH] {line}", end="")

        process.wait()

        return process.returncode == 0, output_lines

    def _get_value_from_output(self, output_lines, prefix):
        for line in output_lines:
            if line.startswith(prefix):
                return line.split(":")
        return None

    def _send_whatsapp_alert_stub(self, message):
        print("[ALERT] WhatsApp alert stub")
        print(f"[ALERT] Message: {message}")

    def _log_failed_attempt(self, rfid_status=None, fingerprint_status=None,
                            face_status=None, behavior_status=None,
                            failure_reason=None):
        log_authentication_attempt(
            employee_id=self.current_employee_id,
            access_session_id=self.current_access_session_id,
            rfid_status=rfid_status,
            fingerprint_status=fingerprint_status,
            face_status=face_status,
            behavior_status=behavior_status,
            final_result="ACCESS_DENIED",
            failure_reason=failure_reason
        )

    def process_authentication(self):
        if self.authentication_completed:
            return False

        print("[AUTH] Starting isolated authentication flow")

        # =========================
        # STEP 1 - RFID
        # =========================
        print("[AUTH] Step 1: RFID")
        rfid_ok, rfid_output = self._run_helper("auth_rfid_only.py")

        if not rfid_ok:
            print("[AUTH] RFID failed")
            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_FAILED",
                failure_reason="RFID authentication failed"
            )
            return False

        rfid_data = self._get_value_from_output(rfid_output, "RFID_OK:")

        if not rfid_data or len(rfid_data) < 2:
            print("[AUTH] RFID returned invalid employee data")
            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_INVALID_DATA",
                failure_reason="RFID returned invalid employee data"
            )
            return False

        rfid_employee_id = int(rfid_data[1])
        self.current_employee_id = rfid_employee_id

        print(f"[AUTH] RFID employee matched: {rfid_employee_id}")

        # =========================
        # STEP 2 - FINGERPRINT
        # =========================
        print("[AUTH] Step 2: Fingerprint")
        finger_ok, finger_output = self._run_helper("auth_fingerprint_only.py")

        if not finger_ok:
            print("[AUTH] Fingerprint process failed")
            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_OK",
                fingerprint_status="FINGER_FAILED",
                failure_reason="Fingerprint authentication failed"
            )
            return False

        finger_data = self._get_value_from_output(finger_output, "FINGER_OK:")

        if not finger_data or len(finger_data) < 4:
            print("[AUTH] Fingerprint returned invalid employee data")
            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_OK",
                fingerprint_status="FINGER_INVALID_DATA",
                failure_reason="Fingerprint returned invalid employee data"
            )
            return False

        finger_employee_id = int(finger_data[1])
        finger_position = finger_data[2]
        finger_accuracy = finger_data[3]

        if finger_employee_id != rfid_employee_id:
            print("[AUTH] Fingerprint employee does not match RFID employee")
            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_OK",
                fingerprint_status="FINGER_EMPLOYEE_MISMATCH",
                failure_reason="Fingerprint employee does not match RFID employee"
            )
            return False

        print(
            f"[AUTH] Fingerprint employee matched: "
            f"{finger_employee_id}, Position: {finger_position}, "
            f"Accuracy: {finger_accuracy}"
        )

        # =========================
        # STEP 3 - FACE RECOGNITION
        # =========================
        print("[AUTH] Step 3: Face Recognition")
        face_ok, face_output = self._run_helper("auth_face_only.py")

        if not face_ok:
            print("[AUTH] Face recognition failed")
            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_OK",
                fingerprint_status="FINGER_OK",
                face_status="FACE_FAILED",
                failure_reason="Face recognition failed"
            )
            return False

        print("[AUTH] Face recognition stage finished")

        # =========================
        # STEP 4 - BEHAVIOR CHECK
        # =========================
        print("[AUTH] Step 4: Dlib Behavior Check")
        behavior_ok, behavior_output = self._run_helper("auth_behavior_only.py")

        if not behavior_ok:
            print("[AUTH] Behavior check danger detected")
            self._send_whatsapp_alert_stub(
                "Danger behavior detected during authentication"
            )

            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_OK",
                fingerprint_status="FINGER_OK",
                face_status="FACE_OK",
                behavior_status="BEHAVIOR_DANGER",
                failure_reason="Danger behavior detected"
            )
            return False

        behavior_status = "BEHAVIOR_UNKNOWN"

        if "BEHAVIOR_MEDIUM" in behavior_output:
            behavior_status = "BEHAVIOR_MEDIUM"
            print("[AUTH] Behavior check medium warning")
            self._send_whatsapp_alert_stub(
                "Medium suspicious behavior detected during authentication"
            )

        elif "BEHAVIOR_NORMAL" in behavior_output:
            behavior_status = "BEHAVIOR_NORMAL"
            print("[AUTH] Behavior check normal")

        else:
            print("[AUTH] Behavior check returned unknown result")
            self.failed_attempts += 1
            self._log_failed_attempt(
                rfid_status="RFID_OK",
                fingerprint_status="FINGER_OK",
                face_status="FACE_OK",
                behavior_status="BEHAVIOR_UNKNOWN",
                failure_reason="Behavior check returned unknown result"
            )
            return False

        print("[AUTH] Behavior check stage finished")

        self.current_access_session_id = start_access_session(
            employee_id=self.current_employee_id
        )

        log_authentication_attempt(
            employee_id=self.current_employee_id,
            access_session_id=self.current_access_session_id,
            rfid_status="RFID_OK",
            fingerprint_status="FINGER_OK",
            face_status="FACE_OK",
            behavior_status=behavior_status,
            final_result="ACCESS_GRANTED",
            failure_reason=None
        )

        print(f"[AUTH] Access session started: {self.current_access_session_id}")
        print(f"[AUTH] Authentication success for EmployeeID: {self.current_employee_id}")

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
