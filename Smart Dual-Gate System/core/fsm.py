import time

from config import settings
from core import states
from hardware import devices
from hardware import indicators
from ai import yolo_room_monitor
from auth import authentication_manager
from database import system_logger
from database.access_session_repository import finish_access_session
from database.security_event_repository import create_security_event
from utils import notification_manager


class MantrapFSM:

    def __init__(self):
        self.current_state = states.SYSTEM_OFF
        self.warning_start_time = None
        self.outer_door_was_opened = False
        self.wait_new_outer_open_after_cancel = False

        self.alarm_level_2_done = False
        self.alarm_level_3_done = False
        self.last_countdown_second = None

    def change_state(self, new_state):
        system_logger.log_info(
            f"State changed: {self.current_state} -> {new_state}"
        )
        self.current_state = new_state

    def reset_warning_data(self):
        self.warning_start_time = None
        self.alarm_level_2_done = False
        self.alarm_level_3_done = False
        self.last_countdown_second = None

    def reset_door_tracking(self):
        self.outer_door_was_opened = False

    def start_system(self):
        devices.set_system_idle_outputs()

        authentication_manager.stop_authentication_modules()
        yolo_room_monitor.stop_room_monitor()

        indicators.stop_alarm()

        self.reset_warning_data()
        self.reset_door_tracking()

        self.change_state(states.IDLE_OUTER_OPEN)
        system_logger.log_info("System started")

    def stop_system(self):
        authentication_manager.stop_authentication_modules()
        yolo_room_monitor.stop_room_monitor()

        devices.lock_both_solenoids()
        devices.set_red_status()
        indicators.stop_alarm()

        self.change_state(states.SYSTEM_OFF)
        system_logger.log_info("System stopped")

    def run_forever(self):
        self.start_system()

        while True:
            try:
                self.run_current_state()
                time.sleep(0.1)

            except KeyboardInterrupt:
                system_logger.log_info("Keyboard interrupt received")
                self.stop_system()
                break

            except Exception as error:
                system_logger.log_error(f"FSM error: {error}")
                self.change_state(states.ERROR_STATE)
                self.stop_system()
                raise

    def run_current_state(self):
        if self.current_state == states.SYSTEM_OFF:
            return

        if self.current_state == states.IDLE_OUTER_OPEN:
            self.handle_idle_outer_open()

        elif self.current_state == states.AI_START_DELAY:
            self.handle_ai_start_delay()

        elif self.current_state == states.PERSON_COUNTING:
            self.handle_person_counting()

        elif self.current_state == states.MULTI_PERSON_WARNING:
            self.handle_multi_person_warning()

        elif self.current_state == states.MULTI_PERSON_EXIT_RELEASE:
            self.handle_multi_person_exit_release()

        elif self.current_state == states.AUTHENTICATION_READY:
            self.handle_authentication_ready()

        elif self.current_state == states.AUTHENTICATION_PROCESSING:
            self.handle_authentication_processing()

        elif self.current_state == states.AUTHENTICATION_FAILED_WAIT_BACK:
            self.handle_authentication_failed_wait_back()

        elif self.current_state == states.WAIT_INNER_BUTTON_CONFIRM:
            self.handle_wait_inner_button_confirm()

        elif self.current_state == states.INNER_DOOR_UNLOCKED:
            self.handle_inner_door_unlocked()

        elif self.current_state == states.CANCEL_AND_EXIT:
            self.handle_cancel_and_exit()

        elif self.current_state == states.SECURITY_LOCKDOWN:
            self.handle_security_lockdown()

        elif self.current_state == states.ERROR_STATE:
            self.handle_error_state()

    def handle_idle_outer_open(self):
        devices.set_red_status()
        devices.unlock_outer_solenoid()
        devices.lock_inner_solenoid()

        if self.wait_new_outer_open_after_cancel:
            if devices.is_outer_door_open():
                self.wait_new_outer_open_after_cancel = False
                self.outer_door_was_opened = True
                system_logger.log_info("New outer door opening detected after cancel")
            return

        if devices.is_outer_door_open():
            self.outer_door_was_opened = True

        if self.outer_door_was_opened and devices.is_outer_door_closed():
            devices.lock_outer_solenoid()
            system_logger.log_info("Outer door closed after opening")

            if devices.are_both_doors_closed():
                self.reset_door_tracking()
                system_logger.log_info("Both doors closed successfully")
                self.change_state(states.AI_START_DELAY)

    def handle_ai_start_delay(self):
        system_logger.log_info("Waiting before YOLO room monitor starts")

        time.sleep(settings.AI_START_DELAY)

        indicators.beep_short()
        yolo_room_monitor.start_room_monitor()

        system_logger.log_info("YOLO room monitor started")
        self.change_state(states.PERSON_COUNTING)

    def handle_person_counting(self):
        detected_count = yolo_room_monitor.get_detected_count()

        system_logger.log_info(
            f"[AI] Detected figures count: {detected_count}"
        )

        if detected_count == 1:
            system_logger.log_info("Exactly one figure detected")
            self.reset_warning_data()
            self.change_state(states.AUTHENTICATION_READY)
            return

        system_logger.log_warning(
            f"Invalid room count detected: {detected_count}"
        )

        create_security_event(
            event_type="INVALID_ROOM_COUNT",
            severity="MEDIUM",
            detected_persons_count=detected_count,
            description=(
                "Invalid room count detected before authentication: "
                f"{detected_count}"
            )
        )

        indicators.beep_alarm_level_1()

        self.reset_warning_data()
        self.warning_start_time = time.time()

        self.change_state(states.MULTI_PERSON_WARNING)

    def handle_multi_person_warning(self):
        detected_count = yolo_room_monitor.get_detected_count()

        if detected_count == 1:
            system_logger.log_info("Room fixed, exactly one figure now")
            indicators.stop_alarm()
            self.reset_warning_data()
            self.change_state(states.AUTHENTICATION_READY)
            return

        if devices.is_back_push_button_pressed():
            system_logger.log_info("Exit release requested")
            indicators.stop_alarm()
            self.change_state(states.MULTI_PERSON_EXIT_RELEASE)
            return

        elapsed_time = time.time() - self.warning_start_time

        if elapsed_time >= 30:
            self.trigger_security_lockdown_from_room_count(detected_count)
            return

        if elapsed_time >= 20 and not self.alarm_level_3_done:
            self.alarm_level_3_done = True
            system_logger.log_warning("Alarm level 3 after 20 seconds")
            indicators.beep_alarm_level_3()
            return

        if elapsed_time >= 10 and not self.alarm_level_2_done:
            self.alarm_level_2_done = True
            system_logger.log_warning("Alarm level 2 after 10 seconds")
            indicators.beep_alarm_level_2()
            return

        if elapsed_time >= 25:
            self.handle_lockdown_countdown(elapsed_time)
            return

        time.sleep(0.2)

    def handle_lockdown_countdown(self, elapsed_time):
        remaining_time = int(30 - elapsed_time)

        if remaining_time != self.last_countdown_second:
            self.last_countdown_second = remaining_time

            system_logger.log_warning(
                f"Lockdown countdown: {remaining_time} seconds"
            )

            devices.start_buzzer()
            time.sleep(0.15)
            devices.stop_buzzer()

    def trigger_security_lockdown_from_room_count(self, detected_count):
        system_logger.log_security(
            f"Danger state: invalid room count still detected: {detected_count}"
        )

        create_security_event(
            event_type="SECURITY_LOCKDOWN",
            severity="HIGH",
            detected_persons_count=detected_count,
            description=(
                "System lockdown triggered because invalid room count remained: "
                f"{detected_count}"
            )
        )

        notification_manager.send_whatsapp_security_alert(
            f"Security alert: invalid room count detected: {detected_count}"
        )

        devices.lock_both_solenoids()
        devices.set_red_status()
        indicators.start_continuous_alarm()

        self.change_state(states.SECURITY_LOCKDOWN)

    def handle_multi_person_exit_release(self):
        system_logger.log_info("Opening outer door for extra person exit")

        devices.lock_inner_solenoid()
        devices.unlock_outer_solenoid()

        start_time = time.time()

        while time.time() - start_time < 10:
            if devices.is_outer_door_open():
                system_logger.log_info("Outer door opened for exit")

                while devices.is_outer_door_open():
                    time.sleep(0.1)

                system_logger.log_info("Outer door closed after exit")

                devices.lock_outer_solenoid()

                yolo_room_monitor.reset_latest_detection()
                time.sleep(2)

                self.reset_warning_data()
                self.change_state(states.PERSON_COUNTING)
                return

            time.sleep(0.1)

        system_logger.log_warning("Exit release timeout")

        devices.lock_outer_solenoid()
        self.reset_warning_data()
        self.change_state(states.PERSON_COUNTING)

    def handle_authentication_ready(self):
        yolo_room_monitor.stop_room_monitor()

        authentication_manager.reset_authentication_session()
        authentication_manager.start_authentication_modules()

        devices.set_green_status()

        system_logger.log_info("Authentication modules activated")

        self.change_state(states.AUTHENTICATION_PROCESSING)

    def handle_authentication_processing(self):
        if not devices.are_both_doors_closed():
            system_logger.log_security("Door opened during authentication")
            self.change_state(states.SECURITY_LOCKDOWN)
            return

        auth_result = authentication_manager.process_authentication()

        if auth_result:
            self.change_state(states.WAIT_INNER_BUTTON_CONFIRM)
            return

        if authentication_manager.is_cancel_requested():
            system_logger.log_info("Authentication cancelled by user")
            self.change_state(states.CANCEL_AND_EXIT)
            return

        system_logger.log_warning(
            "Authentication failed. Cancel button is now enabled."
        )

        if authentication_manager.get_failed_attempts_count() >= settings.MAX_AUTH_ATTEMPTS:
            system_logger.log_security("Maximum authentication attempts reached")
            self.change_state(states.SECURITY_LOCKDOWN)
            return

        self.change_state(states.AUTHENTICATION_FAILED_WAIT_BACK)

    def handle_authentication_failed_wait_back(self):
        if not devices.are_both_doors_closed():
            system_logger.log_security("Door opened after authentication failure")
            self.change_state(states.SECURITY_LOCKDOWN)
            return

        devices.set_red_status()

        system_logger.log_warning(
            "Waiting for cancel button. Press it to cancel and return."
        )

        start_time = time.time()

        while time.time() - start_time < 10:
            if authentication_manager.is_cancel_requested():
                system_logger.log_info("Authentication cancel requested")
                self.change_state(states.CANCEL_AND_EXIT)
                return

            time.sleep(0.1)

        system_logger.log_info(
            "Cancel button was not pressed. Retrying authentication."
        )

        self.change_state(states.AUTHENTICATION_READY)

    def handle_wait_inner_button_confirm(self):
        if not devices.are_both_doors_closed():
            system_logger.log_security("Door opened before confirmation")
            self.change_state(states.SECURITY_LOCKDOWN)
            return

        indicators.beep_success()

        start_time = time.time()

        while time.time() - start_time < settings.INNER_CONFIRM_TIMEOUT:
            devices.turn_green_led_on()
            time.sleep(0.25)

            devices.turn_green_led_off()
            time.sleep(0.25)

            if devices.is_inner_push_button_pressed():
                system_logger.log_access("Inner button confirmed")
                self.change_state(states.INNER_DOOR_UNLOCKED)
                return

        system_logger.log_warning("Inner confirmation timeout")
        self.change_state(states.CANCEL_AND_EXIT)

    def handle_inner_door_unlocked(self):
        if not devices.is_outer_door_closed():
            system_logger.log_security("Outer door is not closed")
            self.change_state(states.SECURITY_LOCKDOWN)
            return

        devices.lock_outer_solenoid()
        devices.unlock_inner_solenoid()

        system_logger.log_access("Inner door unlocked")

        while devices.is_inner_door_closed():
            time.sleep(0.1)

        system_logger.log_info("Inner door opened")

        while devices.is_inner_door_open():
            time.sleep(0.1)

        system_logger.log_info("Inner door closed")

        devices.lock_inner_solenoid()

        self.finish_successful_access()

    def handle_cancel_and_exit(self):
        authentication_manager.stop_authentication_modules()
        yolo_room_monitor.stop_room_monitor()

        devices.set_red_status()
        devices.lock_inner_solenoid()
        devices.unlock_outer_solenoid()

        system_logger.log_info("User exit allowed")

        while devices.is_outer_door_closed():
            time.sleep(0.1)

        system_logger.log_info("Outer door opened")

        while devices.is_outer_door_open():
            time.sleep(0.1)

        system_logger.log_info("Outer door closed again")

        authentication_manager.reset_authentication_session()
        authentication_manager.stop_authentication_modules()
        yolo_room_monitor.stop_room_monitor()

        time.sleep(2)

        devices.lock_inner_solenoid()
        devices.lock_outer_solenoid()
        devices.set_red_status()

        self.reset_warning_data()
        self.reset_door_tracking()

        self.wait_new_outer_open_after_cancel = True

        system_logger.log_info("System returned to idle after cancel")

        self.change_state(states.IDLE_OUTER_OPEN)

    def handle_security_lockdown(self):
        authentication_manager.stop_authentication_modules()
        yolo_room_monitor.stop_room_monitor()

        devices.lock_both_solenoids()
        devices.set_red_status()

        indicators.start_continuous_alarm()

        system_logger.log_security("System lockdown active")

        while True:
            time.sleep(1)

    def handle_error_state(self):
        devices.lock_both_solenoids()
        devices.set_red_status()

        indicators.beep_alarm()

        system_logger.log_error("System entered error state")

        time.sleep(1)

    def finish_successful_access(self):
        access_session_id = (
            authentication_manager.get_current_access_session_id()
        )

        if access_session_id:
            finish_access_session(
                access_session_id=access_session_id,
                exit_method="INNER_DOOR_CLOSED",
                final_status="COMPLETED",
                notes="Access completed successfully"
            )

            system_logger.log_info(
                f"Access session completed: {access_session_id}"
            )

        authentication_manager.stop_authentication_modules()
        yolo_room_monitor.stop_room_monitor()

        devices.set_red_status()
        devices.unlock_outer_solenoid()
        devices.lock_inner_solenoid()

        self.reset_warning_data()
        self.reset_door_tracking()

        system_logger.log_access("Access finished successfully")

        self.change_state(states.IDLE_OUTER_OPEN)
