"""
Read-only door sensor service for the dashboard.
This file reads only limit switch inputs and never controls outputs.
"""

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

from config import settings
from hardware import gpio_map

gpio_ready = False


def _ensure_gpio_inputs():
    global gpio_ready

    if GPIO is None:
        return False

    if gpio_ready:
        return True

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(
            gpio_map.OUTER_LIMIT_SWITCH_PIN,
            GPIO.IN,
            pull_up_down=GPIO.PUD_UP
        )

        GPIO.setup(
            gpio_map.INNER_LIMIT_SWITCH_PIN,
            GPIO.IN,
            pull_up_down=GPIO.PUD_UP
        )

        gpio_ready = True
        return True

    except Exception:
        gpio_ready = False
        return False


def _door_state_from_value(value):
    if value == settings.DOOR_OPEN:
        return "closed"

    if value == settings.DOOR_CLOSED:
        return "open"

    return "unknown"


def read_live_door_states():
    if not _ensure_gpio_inputs():
        return {
            "available": False,
            "outer_door": None,
            "inner_door": None,
        }

    try:
        outer_value = GPIO.input(gpio_map.OUTER_LIMIT_SWITCH_PIN)
        inner_value = GPIO.input(gpio_map.INNER_LIMIT_SWITCH_PIN)

        return {
            "available": True,
            "outer_door": _door_state_from_value(outer_value),
            "inner_door": _door_state_from_value(inner_value),
            "outer_raw": outer_value,
            "inner_raw": inner_value,
        }

    except Exception:
        return {
            "available": False,
            "outer_door": None,
            "inner_door": None,
        }
