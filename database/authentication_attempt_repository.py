from database.database_manager import execute_insert, execute_query


def create_authentication_attempt(
    employee_id=None,
    rfid_status="NOT_STARTED",
    fingerprint_status="NOT_STARTED",
    face_status="NOT_STARTED",
    behavior_status="NOT_STARTED",
    final_result="FAILED",
    failure_reason=None
):
    query = """
        INSERT INTO AuthenticationAttempt
        (
            EmployeeID,
            RFIDStatus,
            FingerprintStatus,
            FaceRecognitionStatus,
            BehaviorStatus,
            FinalResult,
            FailureReason,
            CreationDate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'));
    """

    attempt_id = execute_insert(
        query,
        (
            employee_id,
            rfid_status,
            fingerprint_status,
            face_status,
            behavior_status,
            final_result,
            failure_reason
        )
    )

    if attempt_id:
        print(f"[DATABASE] Authentication attempt saved: {attempt_id}")

    return attempt_id


def get_recent_authentication_attempts(limit=50):
    query = """
        SELECT
            A.AuthenticationAttemptID,
            A.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.SecondName || ' ' || P.ThirdName || ' ' || P.LastName AS FullName,
            A.RFIDStatus,
            A.FingerprintStatus,
            A.FaceRecognitionStatus,
            A.BehaviorStatus,
            A.FinalResult,
            A.FailureReason,
            A.CreationDate
        FROM AuthenticationAttempt A
        LEFT JOIN Employee E ON E.EmployeeID = A.EmployeeID
        LEFT JOIN Person P ON P.PersonID = E.PersonID
        ORDER BY A.AuthenticationAttemptID DESC
        LIMIT ?;
    """

    return execute_query(query, (limit,))


def get_authentication_attempts_by_employee(employee_id, limit=50):
    query = """
        SELECT
            AuthenticationAttemptID,
            EmployeeID,
            RFIDStatus,
            FingerprintStatus,
            FaceRecognitionStatus,
            BehaviorStatus,
            FinalResult,
            FailureReason,
            CreationDate
        FROM AuthenticationAttempt
        WHERE EmployeeID = ?
        ORDER BY AuthenticationAttemptID DESC
        LIMIT ?;
    """

    return execute_query(query, (employee_id, limit))
