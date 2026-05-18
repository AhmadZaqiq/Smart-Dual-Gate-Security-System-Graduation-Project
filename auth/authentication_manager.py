import subprocess
import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "database"))

from authentication_attempt_repository import create_authentication_attempt
from access_session_repository import start_access_session

from system_setting_repository import get_setting_value


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
        create_authentication_attempt(
            employee_id=self.current_employee_id,
            access_session_id=self.current_access_session_id,
            rfid_status=rfid_status,
            fingerprint_status=fingerprint_status,
            face_status=face_status,
            behavior_status=behavior_status,
            final_result="ACCESS_DENIED",
            failure_reason=failure_reason
        )

    def _is_total_attempts_exceeded(self, settings):
        return self.failed_attempts >= settings["max_total_attempts"]

    def process_authentication(self):
        if self.authentication_completed:
            return False

        settings = self._load_auth_settings()

        print("[AUTH] Starting isolated authentication flow")
        print(f"[AUTH] Loaded settings: {settings}")

        rfid_status = "SKIPPED"
        fingerprint_status = "SKIPPED"
        face_status = "SKIPPED"
        behavior_status = "SKIPPED"

        # =========================
        # STEP 1 - RFID
        # =========================
        if settings["require_rfid"]:
            print("[AUTH] Step 1: RFID")

            rfid_ok = False

            for attempt in range(1, settings["max_rfid_attempts"] + 1):
                print(f"[AUTH] RFID attempt {attempt}/{settings['max_rfid_attempts']}")

                helper_ok, rfid_output = self._run_helper("auth_rfid_only.py")

                if helper_ok:
                    rfid_data = self._get_value_from_output(rfid_output, "RFID_OK:")

                    if rfid_data and len(rfid_data) >= 2:
                        rfid_token = rfid_data[1]
                        print(f"[AUTH] RFID shared token accepted: {rfid_token}")
                        rfid_status = "RFID_OK"
                        rfid_ok = True
                        break

                self.failed_attempts += 1
                print("[AUTH] RFID attempt failed")

                if self._is_total_attempts_exceeded(settings):
                    break

            if not rfid_ok:
                self._log_failed_attempt(
                    rfid_status="RFID_FAILED",
                    fingerprint_status=fingerprint_status,
                    face_status=face_status,
                    behavior_status=behavior_status,
                    failure_reason="RFID authentication failed"
                )
                return False

        else:
            print("[AUTH] RFID step skipped by system settings")

        # =========================
        # STEP 2 - FINGERPRINT
        # =========================
        if settings["require_fingerprint"]:
            print("[AUTH] Step 2: Fingerprint")

            fingerprint_ok = False

            for attempt in range(1, settings["max_fingerprint_attempts"] + 1):
                print(f"[AUTH] Fingerprint attempt {attempt}/{settings['max_fingerprint_attempts']}")

                helper_ok, finger_output = self._run_helper("auth_fingerprint_only.py")

                if helper_ok:
                    finger_data = self._get_value_from_output(finger_output, "FINGER_OK:")

                    if finger_data and len(finger_data) >= 4:
                        finger_employee_id = int(finger_data[1])
                        finger_position = finger_data[2]
                        finger_accuracy = finger_data[3]

                        self.current_employee_id = finger_employee_id
                        fingerprint_status = "FINGER_OK"
                        fingerprint_ok = True

                        print(
                            f"[AUTH] Fingerprint employee identified: "
                            f"{finger_employee_id}, Position: {finger_position}, "
                            f"Accuracy: {finger_accuracy}"
                        )
                        break

                self.failed_attempts += 1
                print("[AUTH] Fingerprint attempt failed")

                if self._is_total_attempts_exceeded(settings):
                    break

            if not fingerprint_ok:
                self._log_failed_attempt(
                    rfid_status=rfid_status,
                    fingerprint_status="FINGER_FAILED",
                    face_status=face_status,
                    behavior_status=behavior_status,
                    failure_reason="Fingerprint authentication failed"
                )
                return False

        else:
            print("[AUTH] Fingerprint step skipped by system settings")
            self.current_employee_id = self._get_int_setting("DEFAULT_EMPLOYEE_ID", 1)

        # =========================
        # STEP 3 - FACE RECOGNITION
        # =========================
        if settings["require_face"]:
            print("[AUTH] Step 3: Face Recognition")

            face_ok = False

            for attempt in range(1, settings["max_face_attempts"] + 1):
                print(f"[AUTH] Face recognition attempt {attempt}/{settings['max_face_attempts']}")

                helper_ok, face_output = self._run_helper("auth_face_only.py")

                if helper_ok:
                    face_status = "FACE_OK"
                    face_ok = True
                    print("[AUTH] Face recognition stage finished")
                    break

                self.failed_attempts += 1
                print("[AUTH] Face recognition attempt failed")

                if self._is_total_attempts_exceeded(settings):
                    break

            if not face_ok:
                self._log_failed_attempt(
                    rfid_status=rfid_status,
                    fingerprint_status=fingerprint_status,
                    face_status="FACE_FAILED",
                    behavior_status=behavior_status,
                    failure_reason="Face recognition failed"
                )
                return False

        else:
            print("[AUTH] Face recognition step skipped by system settings")

        # =========================
        # STEP 4 - BEHAVIOR CHECK
        # =========================
        if settings["require_behavior"]:
            print("[AUTH] Step 4: Dlib Behavior Check")

            behavior_ok = False

            for attempt in range(1, settings["max_behavior_attempts"] + 1):
                print(f"[AUTH] Behavior attempt {attempt}/{settings['max_behavior_attempts']}")

                helper_ok, behavior_output = self._run_helper("auth_behavior_only.py")

                if helper_ok:
                    if "BEHAVIOR_MEDIUM" in behavior_output:
                        behavior_status = "BEHAVIOR_MEDIUM"
                        behavior_ok = True
                        print("[AUTH] Behavior check medium warning")
                        self._send_whatsapp_alert_stub(
                            "Medium suspicious behavior detected during authentication"
                        )
                        break

                    if "BEHAVIOR_NORMAL" in behavior_output:
                        behavior_status = "BEHAVIOR_NORMAL"
                        behavior_ok = True
                        print("[AUTH] Behavior check normal")
                        break

                self.failed_attempts += 1
                behavior_status = "BEHAVIOR_DANGER"
                print("[AUTH] Behavior check danger detected")

                self._send_whatsapp_alert_stub(
                    "Danger behavior detected during authentication"
                )

                if self._is_total_attempts_exceeded(settings):
                    break

            if not behavior_ok:
                self._log_failed_attempt(
                    rfid_status=rfid_status,
                    fingerprint_status=fingerprint_status,
                    face_status=face_status,
                    behavior_status=behavior_status,
                    failure_reason="Danger behavior detected"
                )
                return False

        else:
            print("[AUTH] Behavior analysis step skipped by system settings")

        self.current_access_session_id = start_access_session(
            employee_id=self.current_employee_id
        )

        create_authentication_attempt(
            employee_id=self.current_employee_id,
            access_session_id=self.current_access_session_id,
            rfid_status=rfid_status,
            fingerprint_status=fingerprint_status,
            face_status=face_status,
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
