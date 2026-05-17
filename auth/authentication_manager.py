import subprocess
import os


class AuthenticationManager:
    def __init__(self):
        self.auth_dir = os.path.dirname(os.path.abspath(__file__))
        self.failed_attempts = 0
        self.authentication_completed = False

    def start(self):
        print("[AUTH] Authentication modules started")

    def stop(self):
        print("[AUTH] Authentication modules stopped")

    def reset_session(self):
        self.failed_attempts = 0
        self.authentication_completed = False
        print("[AUTH] Authentication session reset")

    def get_failed_attempts(self):
        return self.failed_attempts

    def _run_helper(self, script_name):
        script_path = os.path.join(
            self.auth_dir,
            script_name
        )

        process = subprocess.Popen(
            ["python3", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output_lines = []

        for line in process.stdout:
            output_lines.append(line.strip())
            print(f"[AUTH] {line}", end="")

        process.wait()

        return process.returncode == 0, output_lines

    def _send_whatsapp_alert_stub(self, message):
        print("[ALERT] WhatsApp alert stub")
        print(f"[ALERT] Message: {message}")

    def process_authentication(self):
        if self.authentication_completed:
            return False

        print("[AUTH] Starting isolated authentication flow")

        # =========================
        # STEP 1 - RFID
        # =========================
        print("[AUTH] Step 1: RFID")

        rfid_ok, rfid_output = self._run_helper(
            "auth_rfid_only.py"
        )

        if not rfid_ok:
            print("[AUTH] RFID failed")
            self.failed_attempts += 1
            return False

        print("[AUTH] RFID stage finished")

        # =========================
        # STEP 2 - FINGERPRINT
        # =========================
        print("[AUTH] Step 2: Fingerprint")

        finger_ok, finger_output = self._run_helper(
            "auth_fingerprint_only.py"
        )

        if not finger_ok:
            print("[AUTH] Fingerprint process failed")
            self.failed_attempts += 1
            return False

        print("[AUTH] Fingerprint stage finished")

        # =========================
        # STEP 3 - FACE RECOGNITION
        # =========================
        print("[AUTH] Step 3: Face Recognition")

        face_ok, face_output = self._run_helper(
            "auth_face_only.py"
        )

        if not face_ok:
            print("[AUTH] Face recognition failed")
            self.failed_attempts += 1
            return False

        print("[AUTH] Face recognition stage finished")

        # =========================
        # STEP 4 - BEHAVIOR CHECK
        # =========================
        print("[AUTH] Step 4: Dlib Behavior Check")

        behavior_ok, behavior_output = self._run_helper(
            "auth_behavior_only.py"
        )

        if not behavior_ok:
            print("[AUTH] Behavior check danger detected")

            self._send_whatsapp_alert_stub(
                "Danger behavior detected during authentication"
            )

            self.failed_attempts += 1
            return False

        if "BEHAVIOR_MEDIUM" in behavior_output:
            print("[AUTH] Behavior check medium warning")

            self._send_whatsapp_alert_stub(
                "Medium suspicious behavior detected during authentication"
            )

        elif "BEHAVIOR_NORMAL" in behavior_output:
            print("[AUTH] Behavior check normal")

        else:
            print("[AUTH] Behavior check returned unknown result")
            self.failed_attempts += 1
            return False

        print("[AUTH] Behavior check stage finished")

        print("[AUTH] Authentication success")

        self.authentication_completed = True

        return True


_auth_manager = AuthenticationManager()


# =========================================
# FSM Compatibility Functions
# =========================================

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
