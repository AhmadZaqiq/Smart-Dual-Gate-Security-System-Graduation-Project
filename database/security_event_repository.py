from database.database_manager import execute_insert, execute_query


def create_security_event(event_type, severity="LOW", detected_persons_count=None, description=None, employee_id=None):
    query = """
        INSERT INTO SecurityEvent
        (
            EmployeeID,
            EventType,
            Severity,
            DetectedPersonsCount,
            Description,
            CreationDate
        )
        VALUES (?, ?, ?, ?, ?, datetime('now'));
    """

    event_id = execute_insert(
        query,
        (
            employee_id,
            event_type,
            severity,
            detected_persons_count,
            description
        )
    )

    if event_id:
        print(f"[DATABASE] Security event saved: {event_id}")

    return event_id


def get_recent_security_events(limit=50):
    query = """
        SELECT
            SE.SecurityEventID,
            SE.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.SecondName || ' ' || P.ThirdName || ' ' || P.LastName AS FullName,
            SE.EventType,
            SE.Severity,
            SE.DetectedPersonsCount,
            SE.Description,
            SE.CreationDate
        FROM SecurityEvent SE
        LEFT JOIN Employee E ON E.EmployeeID = SE.EmployeeID
        LEFT JOIN Person P ON P.PersonID = E.PersonID
        ORDER BY SE.SecurityEventID DESC
        LIMIT ?;
    """

    return execute_query(query, (limit,))


def get_security_events_by_type(event_type, limit=50):
    query = """
        SELECT
            SecurityEventID,
            EmployeeID,
            EventType,
            Severity,
            DetectedPersonsCount,
            Description,
            CreationDate
        FROM SecurityEvent
        WHERE EventType = ?
        ORDER BY SecurityEventID DESC
        LIMIT ?;
    """

    return execute_query(query, (event_type, limit))


def get_security_events_by_severity(severity, limit=50):
    query = """
        SELECT
            SecurityEventID,
            EmployeeID,
            EventType,
            Severity,
            DetectedPersonsCount,
            Description,
            CreationDate
        FROM SecurityEvent
        WHERE Severity = ?
        ORDER BY SecurityEventID DESC
        LIMIT ?;
    """

    return execute_query(query, (severity, limit))
