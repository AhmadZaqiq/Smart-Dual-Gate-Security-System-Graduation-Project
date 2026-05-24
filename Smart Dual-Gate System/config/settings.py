# =========================
# MANTRAP SYSTEM SETTINGS
# =========================

SYSTEM_NAME = "Smart Dual-Gate Security System"


# =========================
# Camera Devices
# =========================

FACE_CAM_DEVICE = "/dev/video1"
INNER_CAM_DEVICE = "/dev/video4"


# =========================
# Door Logic
# =========================
# NC Limit Switch Logic
# 0 = Door Closed
# 1 = Door Open
# =========================

DOOR_CLOSED = 0
DOOR_OPEN = 1


# =========================
# Relay Logic
# =========================
# Active LOW Relay Board
# 0 = Relay ON
# 1 = Relay OFF
# =========================

RELAY_ON = 0
RELAY_OFF = 1


# =========================
# Timing Settings
# =========================

AI_START_DELAY = 5

MULTI_PERSON_WARNING_1 = 10
MULTI_PERSON_WARNING_2 = 20

LOCKDOWN_DELAY = 30

INNER_CONFIRM_TIMEOUT = 10


# =========================
# Authentication Settings
# =========================

MAX_AUTH_ATTEMPTS = 2


# =========================
# AI Security Thresholds
# =========================

STRESS_THRESHOLD = 60
ANGER_THRESHOLD = 60
