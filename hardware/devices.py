import RPi.GPIO as GPIO
from config import settings
from hardware import gpio_map


def initialize_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    initialize_outputs()
    initialize_inputs()

    set_system_idle_outputs()


def initialize_outputs():
    GPIO.setup(gpio_map.BUZZER_PIN, GPIO.OUT)

    GPIO.setup(gpio_map.GREEN_LED_PIN, GPIO.OUT)
    GPIO.setup(gpio_map.RED_LED_PIN, GPIO.OUT)

    GPIO.setup(gpio_map.OUTER_SOLENOID_PIN, GPIO.OUT)
    GPIO.setup(gpio_map.INNER_SOLENOID_PIN, GPIO.OUT)


def initialize_inputs():
    GPIO.setup(gpio_map.OUTER_PUSH_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(gpio_map.INNER_PUSH_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(gpio_map.BACK_PUSH_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.setup(gpio_map.INNER_LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(gpio_map.OUTER_LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def set_system_idle_outputs():
    turn_red_led_on()
    turn_green_led_off()
    stop_buzzer()

    unlock_outer_solenoid()
    lock_inner_solenoid()


# =========================
# Door Limit Switches
# =========================

def read_outer_limit_switch():
    return GPIO.input(gpio_map.OUTER_LIMIT_SWITCH_PIN)


def read_inner_limit_switch():
    return GPIO.input(gpio_map.INNER_LIMIT_SWITCH_PIN)


def is_outer_door_closed():
    return read_outer_limit_switch() == settings.DOOR_OPEN


def is_outer_door_open():
    return read_outer_limit_switch() == settings.DOOR_CLOSED


def is_inner_door_closed():
    return read_inner_limit_switch() == settings.DOOR_OPEN


def is_inner_door_open():
    return read_inner_limit_switch() == settings.DOOR_CLOSED


def are_both_doors_closed():
    return is_outer_door_closed() and is_inner_door_closed()


# =========================
# Push Buttons
# =========================

def is_outer_push_button_pressed():
    return GPIO.input(gpio_map.OUTER_PUSH_BUTTON_PIN) == GPIO.LOW


def is_inner_push_button_pressed():
    return GPIO.input(gpio_map.INNER_PUSH_BUTTON_PIN) == GPIO.LOW


def is_back_push_button_pressed():
    return GPIO.input(gpio_map.BACK_PUSH_BUTTON_PIN) == GPIO.HIGH


# =========================
# Solenoids
# =========================

def unlock_outer_solenoid():
    GPIO.output(gpio_map.OUTER_SOLENOID_PIN, settings.RELAY_ON)


def lock_outer_solenoid():
    GPIO.output(gpio_map.OUTER_SOLENOID_PIN, settings.RELAY_OFF)


def unlock_inner_solenoid():
    GPIO.output(gpio_map.INNER_SOLENOID_PIN, settings.RELAY_ON)


def lock_inner_solenoid():
    GPIO.output(gpio_map.INNER_SOLENOID_PIN, settings.RELAY_OFF)


def lock_both_solenoids():
    lock_outer_solenoid()
    lock_inner_solenoid()


# =========================
# LEDs
# =========================

def turn_red_led_on():
    GPIO.output(gpio_map.RED_LED_PIN, GPIO.HIGH)


def turn_red_led_off():
    GPIO.output(gpio_map.RED_LED_PIN, GPIO.LOW)


def turn_green_led_on():
    GPIO.output(gpio_map.GREEN_LED_PIN, GPIO.HIGH)


def turn_green_led_off():
    GPIO.output(gpio_map.GREEN_LED_PIN, GPIO.LOW)


def set_red_status():
    turn_red_led_on()
    turn_green_led_off()


def set_green_status():
    turn_green_led_on()
    turn_red_led_off()


# =========================
# Buzzer
# =========================

def start_buzzer():
    GPIO.output(gpio_map.BUZZER_PIN, GPIO.HIGH)


def stop_buzzer():
    GPIO.output(gpio_map.BUZZER_PIN, GPIO.LOW)


def cleanup_gpio():
    lock_both_solenoids()
    turn_red_led_off()
    turn_green_led_off()
    stop_buzzer()
    GPIO.cleanup()
