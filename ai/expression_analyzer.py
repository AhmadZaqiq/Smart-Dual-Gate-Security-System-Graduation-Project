# Temporary expression analyzer placeholder
# Later this file will analyze stress / anger from FaceCam.

def start_expression_analysis():
    print("[AI] Expression analysis started")


def stop_expression_analysis():
    print("[AI] Expression analysis stopped")


def get_stress_percentage():
    return 10


def get_anger_percentage():
    return 10


def is_expression_safe(stress_threshold, anger_threshold):
    stress = get_stress_percentage()
    anger = get_anger_percentage()

    return stress < stress_threshold and anger < anger_threshold
