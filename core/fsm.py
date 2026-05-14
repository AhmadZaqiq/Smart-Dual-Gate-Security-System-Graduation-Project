import time

from config import settings
from core import states
from hardware import devices
from hardware import indicators
from ai import person_counter
from ai import expression_analyzer
from auth import authentication_manager
from database import system_logger


class MantrapFSM:
    def __init__(self):
        self.current_state = states.SYSTEM_OFF
        self.warning_start_time = None

        # لازم الباب الخارجي ينفتح أولًا
        self.outer_door_was_opened = False

    def change_state(self, new_state):
        system_logger.log_info(
            f"State changed: {self.current_state} -> {new_state}"
        )

        self.current_state = new_state

    def start_system(self):
        devices.set_system_idle_outputs()

        authentication_manager.stop_authentication_modules()
        person_counter.stop_person_counting()
        expression_analyzer.stop_expression_analysis()

        self.outer_door_was_opened = False

        self.change_state(states.IDLE_OUTER_OPEN)

        system_logger.log_info("System started")

    def stop_system(self):
        authentication_manager.stop_authentication_modules()

        person_counter.stop_person_counting()

        expression_analyzer.stop_expression_analysis()

        devices.lock_both_solenoids()
        devices.set_red_status()

        self.change_state(states.SYSTEM_OFF)

        system_logger.log_info("System stopped")

    def run_forever(self):
        self.start_system()

        while True:
            try:
                self.run_current_state()

                time.sleep(0.1)

            except KeyboardInterrupt:
                system_logger.log_info(
                    "Keyboard interrupt received"
                )

                break

            except Exception as error:
                system_logger.log_error(
                    f"FSM error: {error}"
                )

                self.change_state(states.ERROR_STATE)

        self.stop_system()

    def run_current_state(self):
        if self.current_state == states.SYSTEM_OFF:
            return

        elif self.current_state == states.IDLE_OUTER_OPEN:
            self.handle_idle_outer_open()

        elif self.current_state == states.AI_START_DELAY:
            self.handle_ai_start_delay()

        elif self.current_state == states.PERSON_COUNTING:
            self.handle_person_counting()

        elif self.current_state == states.MULTI_PERSON_WARNING:
            self.handle_multi_person_warning()

        elif self.current_state == states.AUTHENTICATION_READY:
            self.handle_authentication_ready()

        elif self.current_state == states.AUTHENTICATION_PROCESSING:
            self.handle_authentication_processing()

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

    # =========================
    # IDLE
    # =========================

    def handle_idle_outer_open(self):
        devices.set_red_status()

        # الخارجي مفتوح
        devices.unlock_outer_solenoid()

        # الداخلي دائمًا مغلق
        devices.lock_inner_solenoid()

        # إذا الباب الخارجي انفتح فعليًا
        if devices.is_outer_door_open():
            self.outer_door_was_opened = True

        # نبدأ فقط إذا:
        # الباب انفتح وبعدها تسكر
        if (
            self.outer_door_was_opened
            and devices.is_outer_door_closed()
        ):
            devices.lock_outer_solenoid()

            system_logger.log_info(
                "Outer door closed after opening"
            )

            if devices.are_both_doors_closed():

                self.outer_door_was_opened = False

                system_logger.log_info(
                    "Both doors closed successfully"
                )

                self.change_state(states.AI_START_DELAY)

            else:
                system_logger.log_warning(
                    "Both doors are not closed"
                )

    # =========================
    # AI START DELAY
    # =========================

    def handle_ai_start_delay(self):
        system_logger.log_info(
            "Waiting before AI starts"
        )

        time.sleep(settings.AI_START_DELAY)

        indicators.beep_short()

        person_counter.start_person_counting()

        self.change_state(states.PERSON_COUNTING)

    # =========================
    # PERSON COUNTING
    # =========================

    def handle_person_counting(self):
        if person_counter.is_unknown_object_detected():

            system_logger.log_security(
                "Unknown object detected"
            )

            self.change_state(states.SECURITY_LOCKDOWN)

            return

        if person_counter.is_multiple_persons_detected():

            system_logger.log_warning(
                "Multiple persons detected"
            )

            self.warning_start_time = time.time()

            self.change_state(
                states.MULTI_PERSON_WARNING
            )

            return

        if person_counter.is_exactly_one_person_detected():

            system_logger.log_info(
                "Exactly one person detected"
            )

            self.change_state(
                states.AUTHENTICATION_READY
            )

    # =========================
    # MULTI PERSON WARNING
    # =========================

    def handle_multi_person_warning(self):
        if devices.is_back_push_button_pressed():

            system_logger.log_info(
                "Back button pressed"
            )

            self.change_state(states.CANCEL_AND_EXIT)

            return

        elapsed_time = (
            time.time() - self.warning_start_time
        )

        if elapsed_time >= settings.LOCKDOWN_DELAY:

            system_logger.log_security(
                "Lockdown triggered"
            )

            self.change_state(
                states.SECURITY_LOCKDOWN
            )

            return

        if elapsed_time >= settings.MULTI_PERSON_WARNING_2:
            indicators.beep_alarm()

        elif elapsed_time >= settings.MULTI_PERSON_WARNING_1:
            indicators.beep_warning()

    # =========================
    # AUTH READY
    # =========================

    def handle_authentication_ready(self):
        person_counter.stop_person_counting()

        authentication_manager.reset_authentication_session()

        authentication_manager.start_authentication_modules()

        expression_analyzer.start_expression_analysis()

        devices.set_green_status()

        system_logger.log_info(
            "Authentication modules activated"
        )

        self.change_state(
            states.AUTHENTICATION_PROCESSING
        )

    # =========================
    # AUTH PROCESSING
    # =========================

    def handle_authentication_processing(self):
        if not devices.are_both_doors_closed():

            system_logger.log_security(
                "Door opened during authentication"
            )

            self.change_state(
                states.SECURITY_LOCKDOWN
            )

            return

        if devices.is_outer_push_button_pressed():

            system_logger.log_info(
                "User cancelled authentication"
            )

            self.change_state(
                states.CANCEL_AND_EXIT
            )

            return

        if not expression_analyzer.is_expression_safe(
            settings.STRESS_THRESHOLD,
            settings.ANGER_THRESHOLD
        ):
            system_logger.log_security(
                "Unsafe facial expression"
            )

            self.change_state(
                states.SECURITY_LOCKDOWN
            )

            return

        auth_result = (
            authentication_manager.process_authentication()
        )

        if auth_result:

            self.change_state(
                states.WAIT_INNER_BUTTON_CONFIRM
            )

            return

        if (
            authentication_manager.get_failed_attempts_count()
            >= settings.MAX_AUTH_ATTEMPTS
        ):
            system_logger.log_security(
                "Maximum authentication attempts reached"
            )

            self.change_state(
                states.SECURITY_LOCKDOWN
            )

    # =========================
    # INNER BUTTON CONFIRM
    # =========================

    def handle_wait_inner_button_confirm(self):
        if not devices.are_both_doors_closed():

            system_logger.log_security(
                "Door opened before confirmation"
            )

            self.change_state(
                states.SECURITY_LOCKDOWN
            )

            return

        indicators.beep_success()

        start_time = time.time()

        while (
            time.time() - start_time
            < settings.INNER_CONFIRM_TIMEOUT
        ):
            devices.turn_green_led_on()
            time.sleep(0.25)

            devices.turn_green_led_off()
            time.sleep(0.25)

            if devices.is_inner_push_button_pressed():

                system_logger.log_access(
                    "Inner button confirmed"
                )

                self.change_state(
                    states.INNER_DOOR_UNLOCKED
                )

                return

        system_logger.log_warning(
            "Inner confirmation timeout"
        )

        self.change_state(states.CANCEL_AND_EXIT)

    # =========================
    # INNER DOOR UNLOCK
    # =========================

    def handle_inner_door_unlocked(self):
        if not devices.is_outer_door_closed():

            system_logger.log_security(
                "Outer door is not closed"
            )

            self.change_state(
                states.SECURITY_LOCKDOWN
            )

            return

        devices.lock_outer_solenoid()

        devices.unlock_inner_solenoid()

        system_logger.log_access(
            "Inner door unlocked"
        )

        while devices.is_inner_door_closed():
            time.sleep(0.1)

        system_logger.log_info(
            "Inner door opened"
        )

        while devices.is_inner_door_open():
            time.sleep(0.1)

        system_logger.log_info(
            "Inner door closed"
        )

        devices.lock_inner_solenoid()

        self.finish_successful_access()

    # =========================
    # CANCEL AND EXIT
    # =========================

    def handle_cancel_and_exit(self):
        authentication_manager.stop_authentication_modules()

        expression_analyzer.stop_expression_analysis()

        person_counter.stop_person_counting()

        devices.set_red_status()

        devices.lock_inner_solenoid()

        devices.unlock_outer_solenoid()

        system_logger.log_info(
            "User exit allowed"
        )

        while devices.is_outer_door_closed():
            time.sleep(0.1)

        system_logger.log_info(
            "Outer door opened"
        )

        while devices.is_outer_door_open():
            time.sleep(0.1)

        system_logger.log_info(
            "Outer door closed again"
        )

        devices.lock_outer_solenoid()

        self.start_system()

    # =========================
    # LOCKDOWN
    # =========================

    def handle_security_lockdown(self):
        authentication_manager.stop_authentication_modules()

        expression_analyzer.stop_expression_analysis()

        person_counter.stop_person_counting()

        devices.lock_both_solenoids()

        devices.set_red_status()

        indicators.beep_alarm()

        system_logger.log_security(
            "System lockdown active"
        )

        while True:
            time.sleep(1)

    # =========================
    # ERROR
    # =========================

    def handle_error_state(self):
        devices.lock_both_solenoids()

        devices.set_red_status()

        indicators.beep_alarm()

        system_logger.log_error(
            "System entered error state"
        )

        time.sleep(1)

    # =========================
    # FINISH ACCESS
    # =========================

    def finish_successful_access(self):
        authentication_manager.stop_authentication_modules()

        expression_analyzer.stop_expression_analysis()

        person_counter.stop_person_counting()

        devices.set_red_status()

        devices.unlock_outer_solenoid()

        devices.lock_inner_solenoid()

        system_logger.log_access(
            "Access finished successfully"
        )

        self.change_state(
            states.IDLE_OUTER_OPEN
        )
