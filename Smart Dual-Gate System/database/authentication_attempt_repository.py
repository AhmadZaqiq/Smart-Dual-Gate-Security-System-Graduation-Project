from database.database_manager import (
    execute_insert,
    execute_query,
    execute_query_one
)


def create_authentication_attempt(
    access_session_id=None,
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
            AccessSessionID,
            EmployeeID,
            RFIDStatus,
            FingerprintStatus,
            FaceRecognitionStatus,
            BehaviorStatus,
            FinalResult,
            FailureReason,
            CreationDate
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            datetime('now')
        );
    """

    attempt_id = execute_insert(
        query,
        (
            access_session_id,
            employee_id,
            rfid_status,
            fingerprint_status,
            face_status,
            behavior_status,
            final_result,
            failure_reason
        )
    )

    print(f"[DATABASE] Authentication attempt saved: {attempt_id}", flush=True)

    return attempt_id


def get_recent_authentication_attempts(limit=50):
    query = """
        SELECT
            A.AuthenticationAttemptID,
            A.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
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


def get_authentication_attempt_by_id(authentication_attempt_id):
    query = """
        SELECT
            A.*,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.LastName AS FullName
        FROM AuthenticationAttempt A
        LEFT JOIN Employee E ON E.EmployeeID = A.EmployeeID
        LEFT JOIN Person P ON P.PersonID = E.PersonID
        WHERE A.AuthenticationAttemptID = ?;
    """

    return execute_query_one(query, (authentication_attempt_id,))


def get_authentication_attempts_paginated(
    page=1,
    limit=25,
    final_result=None,
    search_text=None,
    employee_id=None
):
    filters = []
    params = []

    if final_result:
        filters.append("A.FinalResult = ?")
        params.append(final_result)

    if employee_id:
        filters.append("A.EmployeeID = ?")
        params.append(employee_id)

    if search_text:
        filters.append(
            "(E.EmployeeNumber LIKE ? OR P.FirstName LIKE ? OR P.LastName LIKE ?)"
        )
        value = f"%{search_text}%"
        params.extend([value, value, value])

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    offset = (page - 1) * limit

    query = f"""
        SELECT
            A.AuthenticationAttemptID,
            A.AccessSessionID,
            A.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.LastName AS FullName,
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
        {where_clause}
        ORDER BY A.AuthenticationAttemptID DESC
        LIMIT ? OFFSET ?;
    """

    params.extend([limit, offset])

    return execute_query(query, tuple(params))


def count_authentication_attempts(
    final_result=None,
    search_text=None,
    employee_id=None
):
    filters = []
    params = []

    if final_result:
        filters.append("FinalResult = ?")
        params.append(final_result)

    if employee_id:
        filters.append("EmployeeID = ?")
        params.append(employee_id)

    if search_text:
        filters.append(
            "(EmployeeID IN ("
            "SELECT E.EmployeeID FROM Employee E "
            "INNER JOIN Person P ON P.PersonID = E.PersonID "
            "WHERE E.EmployeeNumber LIKE ? "
            "OR P.FirstName LIKE ? OR P.LastName LIKE ?))"
        )
        value = f"%{search_text}%"
        params.extend([value, value, value])

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query = f"SELECT COUNT(*) AS Total FROM AuthenticationAttempt {where_clause};"

    result = execute_query_one(query, tuple(params))

    if result:
        return result["Total"]

    return 0
