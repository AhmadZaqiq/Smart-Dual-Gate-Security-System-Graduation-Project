# =========================
# MANTRAP SYSTEM SETTINGS
# =========================

SYSTEM_NAME = "Smart Dual-Gate Security System"

# Camera devices
FACE_CAM_DEVICE = "/dev/video0"
INNER_CAM_DEVICE = "/dev/video2"

# Door logic
DOOR_CLOSED = 0
DOOR_OPEN = 1

# Relay logic
RELAY_ON = 0
RELAY_OFF = 1

# Timing
AI_START_DELAY = 5
MULTI_PERSON_WARNING_1 = 10
MULTI_PERSON_WARNING_2 = 20
LOCKDOWN_DELAY = 30
INNER_CONFIRM_TIMEOUT = 5

# Authentication
MAX_AUTH_ATTEMPTS = 2

# AI thresholds
STRESS_THRESHOLD = 60
ANGER_THRESHOLD = 60
