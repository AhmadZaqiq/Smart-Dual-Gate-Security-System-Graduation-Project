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

            try:
                notification_manager.send_email_security_alert(
                    message=f"Maximum authentication attempts reached: {settings.MAX_AUTH_ATTEMPTS}",
                    alert_title="Authentication Limit Exceeded",
                    severity="HIGH",
                    include_snapshots=True
                )
            except Exception:
                pass

            devices.lock_both_solenoids()
            devices.set_red_status()
            indicators.start_continuous_alarm()

            self.change_state(states.SECURITY_LOCKDOWN)
            return

        self.change_state(states.AUTHENTICATION_FAILED_WAIT_BACK)
