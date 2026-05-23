from database.database_manager import (
    execute_insert,
    execute_non_query,
    execute_query,
    execute_query_one
)


def create_security_event(event_type, severity="LOW",
                          detected_persons_count=None,
                          description=None,
                          employee_id=None):
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
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            datetime('now')
        );
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
        print(f"[DATABASE] Security event saved: {event_id}", flush=True)

    return event_id


def get_recent_security_events(limit=50):
    query = """
        SELECT
            SE.SecurityEventID,
            SE.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
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


def get_security_event_by_id(security_event_id):
    query = """
        SELECT
            SE.*,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.LastName AS EmployeeName,
            A.UserName AS ResolvedByUsername
        FROM SecurityEvent SE
        LEFT JOIN Employee E ON E.EmployeeID = SE.EmployeeID
        LEFT JOIN Person P ON P.PersonID = E.PersonID
        LEFT JOIN AdminUser A ON A.AdminUserID = SE.ResolvedByAdminUserID
        WHERE SE.SecurityEventID = ?;
    """

    return execute_query_one(query, (security_event_id,))


def resolve_security_event(security_event_id, admin_user_id, notes=None):
    query = """
        UPDATE SecurityEvent
        SET
            IsResolved = 1,
            ResolvedByAdminUserID = ?,
            ResolvedDate = datetime('now'),
            Description = COALESCE(?, Description),
            LastUpdatedDate = datetime('now')
        WHERE SecurityEventID = ?;
    """

    rows = execute_non_query(
        query,
        (admin_user_id, notes, security_event_id)
    )

    return rows > 0


def get_security_events_paginated(
    page=1,
    limit=25,
    severity=None,
    event_type=None,
    resolved=None,
    search_text=None
):
    filters = []
    params = []

    if severity:
        filters.append("SE.Severity = ?")
        params.append(severity)

    if event_type:
        filters.append("SE.EventType = ?")
        params.append(event_type)

    if resolved is not None:
        filters.append("SE.IsResolved = ?")
        params.append(1 if resolved else 0)

    if search_text:
        filters.append(
            "(SE.EventType LIKE ? OR SE.Description LIKE ? OR SE.Severity LIKE ?)"
        )
        value = f"%{search_text}%"
        params.extend([value, value, value])

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    offset = (page - 1) * limit

    query = f"""
        SELECT
            SE.SecurityEventID,
            SE.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.LastName AS FullName,
            SE.EventType,
            SE.Severity,
            SE.DetectedPersonsCount,
            SE.Description,
            SE.IsResolved,
            SE.CreationDate
        FROM SecurityEvent SE
        LEFT JOIN Employee E ON E.EmployeeID = SE.EmployeeID
        LEFT JOIN Person P ON P.PersonID = E.PersonID
        {where_clause}
        ORDER BY SE.SecurityEventID DESC
        LIMIT ? OFFSET ?;
    """

    params.extend([limit, offset])

    return execute_query(query, tuple(params))


def count_security_events(
    severity=None,
    event_type=None,
    resolved=None,
    search_text=None
):
    filters = []
    params = []

    if severity:
        filters.append("Severity = ?")
        params.append(severity)

    if event_type:
        filters.append("EventType = ?")
        params.append(event_type)

    if resolved is not None:
        filters.append("IsResolved = ?")
        params.append(1 if resolved else 0)

    if search_text:
        filters.append("(EventType LIKE ? OR Description LIKE ? OR Severity LIKE ?)")
        value = f"%{search_text}%"
        params.extend([value, value, value])

    where_clause = ""

    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query = f"SELECT COUNT(*) AS Total FROM SecurityEvent {where_clause};"

    result = execute_query_one(query, tuple(params))

    if result:
        return result["Total"]

    return 0
