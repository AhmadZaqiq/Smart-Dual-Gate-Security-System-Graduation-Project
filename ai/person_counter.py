# Temporary AI placeholder
# Later this file will be replaced with the real trained model logic.

def start_person_counting():
    print("[AI] Person counting started")


def stop_person_counting():
    print("[AI] Person counting stopped")


def get_person_count_result():
    # Temporary result for testing FSM
    # Change this number manually during tests:
    # 1 = one person
    # 2 = multiple persons
    # 0 = no person / object issue
    return 1


def is_exactly_one_person_detected():
    return get_person_count_result() == 1


def is_multiple_persons_detected():
    return get_person_count_result() > 1


def is_unknown_object_detected():
    return get_person_count_result() == 0
