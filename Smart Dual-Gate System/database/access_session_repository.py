from database.database_manager import (
    execute_insert,
    execute_non_query,
    execute_query,
    execute_query_one
)


def start_access_session(employee_id, entry_method="FULL_AUTHENTICATION", notes=None):
    query = """
        INSERT INTO AccessSession
        (
            EmployeeID,
            EntryTime,
            EntryMethod,
            FinalStatus,
            Notes,
            CreationDate,
            LastUpdatedDate
        )
        VALUES
        (
            ?,
            datetime('now'),
            ?,
            'ACTIVE',
            ?,
            datetime('now'),
            datetime('now')
        );
    """

    session_id = execute_insert(
        query,
        (employee_id, entry_method, notes)
    )

    if session_id:
        print(f"[DATABASE] Access session started: {session_id}", flush=True)

    return session_id


def finish_access_session(access_session_id, final_status="COMPLETED",
                          exit_method="INNER_DOOR_CLOSED", notes=None):
    query = """
        UPDATE AccessSession
        SET
            ExitTime = datetime('now'),
            SessionDurationSeconds = CAST(
                (julianday(datetime('now')) - julianday(EntryTime)) * 86400
                AS INTEGER
            ),
            FinalStatus = ?,
            ExitMethod = ?,
            Notes = COALESCE(?, Notes),
            LastUpdatedDate = datetime('now')
        WHERE AccessSessionID = ?;
    """

    rows = execute_non_query(
        query,
        (final_status, exit_method, notes, access_session_id)
    )

    if rows > 0:
        print(f"[DATABASE] Access session finished: {access_session_id}", flush=True)

    return rows > 0


def get_access_session_by_id(access_session_id):
    query = """
        SELECT
            S.AccessSessionID,
            S.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
            S.EntryTime,
            S.ExitTime,
            S.SessionDurationSeconds,
            S.EntryMethod,
            S.ExitMethod,
            S.FinalStatus,
            S.Notes
        FROM AccessSession S
        LEFT JOIN Employee E ON E.EmployeeID = S.EmployeeID
        LEFT JOIN Person P ON P.PersonID = E.PersonID
        WHERE S.AccessSessionID = ?;
    """

    return execute_query_one(query, (access_session_id,))


def get_recent_access_sessions(limit=50):
    query = """
        SELECT
            S.AccessSessionID,
            S.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
            S.EntryTime,
            S.ExitTime,
            S.SessionDurationSeconds,
            S.EntryMethod,
            S.ExitMethod,
            S.FinalStatus,
            S.Notes
        FROM AccessSession S
        LEFT JOIN Employee E ON E.EmployeeID = S.EmployeeID
        LEFT JOIN Person P ON P.PersonID = E.PersonID
        ORDER BY S.AccessSessionID DESC
        LIMIT ?;
    """

    return execute_query(query, (limit,))


def get_access_sessions_by_employee(employee_id, limit=50):
    query = """
        SELECT
            AccessSessionID,
            EmployeeID,
            EntryTime,
            ExitTime,
            SessionDurationSeconds,
            EntryMethod,
            ExitMethod,
            FinalStatus,
            Notes
        FROM AccessSession
        WHERE EmployeeID = ?
        ORDER BY AccessSessionID DESC
        LIMIT ?;
    """

    return execute_query(query, (employee_id, limit))


def get_active_access_session_by_employee(employee_id):
    query = """
        SELECT
            AccessSessionID,
            EmployeeID,
            EntryTime,
            EntryMethod,
            FinalStatus
        FROM AccessSession
        WHERE EmployeeID = ?
          AND FinalStatus = 'ACTIVE'
        ORDER BY AccessSessionID DESC
        LIMIT 1;
    """

    return execute_query_one(query, (employee_id,))
