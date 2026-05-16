import time

from hardware import devices


def beep_short():
    devices.start_buzzer()
    time.sleep(0.15)
    devices.stop_buzzer()


def beep_success():
    for _ in range(2):
        devices.start_buzzer()
        time.sleep(0.12)
        devices.stop_buzzer()
        time.sleep(0.12)


def beep_warning():
    for _ in range(3):
        devices.start_buzzer()
        time.sleep(0.2)
        devices.stop_buzzer()
        time.sleep(0.15)


def beep_alarm():
    for _ in range(8):
        devices.start_buzzer()
        time.sleep(0.25)
        devices.stop_buzzer()
        time.sleep(0.1)


def beep_alarm_level_1():
    devices.start_buzzer()
    time.sleep(0.5)
    devices.stop_buzzer()


def beep_alarm_level_2():
    devices.start_buzzer()
    time.sleep(1)
    devices.stop_buzzer()


def beep_alarm_level_3():
    for _ in range(2):
        devices.start_buzzer()
        time.sleep(0.5)
        devices.stop_buzzer()
        time.sleep(0.15)


def beep_every_second(seconds=5):
    for _ in range(seconds):
        devices.start_buzzer()
        time.sleep(0.15)
        devices.stop_buzzer()
        time.sleep(0.85)


def start_continuous_alarm():
    devices.start_buzzer()


def stop_alarm():
    devices.stop_buzzer()


def blink_green_led_for_confirmation(seconds=5):
    start_time = time.time()

    while time.time() - start_time < seconds:
        devices.turn_green_led_on()
        time.sleep(0.25)

        devices.turn_green_led_off()
        time.sleep(0.25)


def blink_red_led_warning(seconds=5):
    start_time = time.time()

    while time.time() - start_time < seconds:
        devices.turn_red_led_on()
        time.sleep(0.25)

        devices.turn_red_led_off()
        time.sleep(0.25)

    devices.turn_red_led_on()
