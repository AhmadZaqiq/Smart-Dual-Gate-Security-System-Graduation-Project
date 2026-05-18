from pprint import pprint

from database.employee_repository import *
from database.employee_auth_repository import *
from database.access_session_repository import *
from database.authentication_attempt_repository import *
from database.security_event_repository import *
from database.dashboard_repository import *


print("\n========== EMPLOYEES ==========")
pprint(get_all_employees())

print("\n========== EMPLOYEE BY RFID ==========")

print("\n========== EMPLOYEE BY FINGERPRINT ==========")
pprint(get_employee_by_fingerprint_position(0))

print("\n========== ACCESS SESSIONS ==========")
pprint(get_recent_access_sessions())

print("\n========== AUTH ATTEMPTS ==========")
pprint(get_recent_authentication_attempts())

print("\n========== SECURITY EVENTS ==========")
pprint(get_recent_security_events())

print("\n========== DASHBOARD SUMMARY ==========")
pprint(get_dashboard_summary())

print("\n========== RECENT ACTIVITY ==========")
pprint(get_recent_activity())

