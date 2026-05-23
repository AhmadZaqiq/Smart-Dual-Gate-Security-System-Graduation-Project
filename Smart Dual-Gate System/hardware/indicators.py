import time

from hardware import devices

SHORT_BEEP_DURATION = 0.15

SUCCESS_BEEP_DURATION = 0.12
SUCCESS_BEEP_DELAY = 0.12

WARNING_BEEP_DURATION = 0.2
WARNING_BEEP_DELAY = 0.15

ALARM_BEEP_DURATION = 0.25
ALARM_BEEP_DELAY = 0.1

LEVEL_1_DURATION = 0.5
LEVEL_2_DURATION = 1.0

LEVEL_3_DURATION = 0.5
LEVEL_3_DELAY = 0.15

COUNTDOWN_BEEP_DURATION = 0.15
COUNTDOWN_BEEP_DELAY = 0.85

LED_BLINK_DURATION = 0.25


# =========================
# Generic Buzzer Helpers
# =========================

def single_beep(duration):
    devices.start_buzzer()
    time.sleep(duration)
    devices.stop_buzzer()


def repeated_beep(count, duration, delay):
    for _ in range(count):
        devices.start_buzzer()
        time.sleep(duration)

        devices.stop_buzzer()
        time.sleep(delay)


# =========================
# Normal Sounds
# =========================

def beep_short():
    single_beep(SHORT_BEEP_DURATION)


def beep_success():
    repeated_beep(
        count=2,
        duration=SUCCESS_BEEP_DURATION,
        delay=SUCCESS_BEEP_DELAY
    )


def beep_warning():
    repeated_beep(
        count=3,
        duration=WARNING_BEEP_DURATION,
        delay=WARNING_BEEP_DELAY
    )


def beep_alarm():
    repeated_beep(
        count=8,
        duration=ALARM_BEEP_DURATION,
        delay=ALARM_BEEP_DELAY
    )


# =========================
# Security Alarm Levels
# =========================

def beep_alarm_level_1():
    single_beep(LEVEL_1_DURATION)


def beep_alarm_level_2():
    single_beep(LEVEL_2_DURATION)


def beep_alarm_level_3():
    repeated_beep(
        count=2,
        duration=LEVEL_3_DURATION,
        delay=LEVEL_3_DELAY
    )


def beep_every_second(seconds=5):
    for _ in range(seconds):
        devices.start_buzzer()

        time.sleep(COUNTDOWN_BEEP_DURATION)

        devices.stop_buzzer()

        time.sleep(COUNTDOWN_BEEP_DELAY)


def start_continuous_alarm():
    devices.start_buzzer()


def stop_alarm():
    devices.stop_buzzer()


# =========================
# LED Indicators
# =========================

def blink_green_led_for_confirmation(seconds=5):
    start_time = time.time()

    while time.time() - start_time < seconds:
        devices.turn_green_led_on()
        time.sleep(LED_BLINK_DURATION)

        devices.turn_green_led_off()
        time.sleep(LED_BLINK_DURATION)


def blink_red_led_warning(seconds=5):
    start_time = time.time()

    while time.time() - start_time < seconds:
        devices.turn_red_led_on()
        time.sleep(LED_BLINK_DURATION)

        devices.turn_red_led_off()
        time.sleep(LED_BLINK_DURATION)

    devices.turn_red_led_on()


def beep_error():
    single_beep(0.35)
