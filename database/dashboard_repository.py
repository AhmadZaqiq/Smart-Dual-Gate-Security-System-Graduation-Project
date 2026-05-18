from database.database_manager import execute_query, execute_query_one


def get_dashboard_summary():
    query = """
        SELECT
            (SELECT COUNT(*) FROM Employee WHERE IsDeleted = 0) AS TotalEmployees,
            (SELECT COUNT(*) FROM Employee WHERE IsActive = 1 AND IsDeleted = 0) AS ActiveEmployees,
            (SELECT COUNT(*) FROM AccessSession WHERE FinalStatus = 'COMPLETED') AS CompletedSessions,
            (SELECT COUNT(*) FROM AccessSession WHERE FinalStatus = 'ACTIVE') AS ActiveSessions,
            (SELECT COUNT(*) FROM AuthenticationAttempt WHERE FinalResult = 'SUCCESS') AS SuccessfulAuthentications,
            (SELECT COUNT(*) FROM AuthenticationAttempt WHERE FinalResult = 'FAILED') AS FailedAuthentications,
            (SELECT COUNT(*) FROM SecurityEvent) AS SecurityEvents;
    """

    return execute_query_one(query)


def get_today_access_count():
    query = """
        SELECT COUNT(*) AS TodayAccessCount
        FROM AccessSession
        WHERE date(EntryTime) = date('now');
    """

    result = execute_query_one(query)
    return result["TodayAccessCount"] if result else 0


def get_today_security_events_count():
    query = """
        SELECT COUNT(*) AS TodaySecurityEventsCount
        FROM SecurityEvent
        WHERE date(CreationDate) = date('now');
    """

    result = execute_query_one(query)
    return result["TodaySecurityEventsCount"] if result else 0


def get_recent_activity(limit=20):
    query = """
        SELECT
            'ACCESS_SESSION' AS ActivityType,
            AccessSessionID AS RecordID,
            FinalStatus AS Title,
            EntryTime AS CreationDate
        FROM AccessSession

        UNION ALL

        SELECT
            'SECURITY_EVENT' AS ActivityType,
            SecurityEventID AS RecordID,
            EventType AS Title,
            CreationDate
        FROM SecurityEvent

        UNION ALL

        SELECT
            'AUTHENTICATION_ATTEMPT' AS ActivityType,
            AuthenticationAttemptID AS RecordID,
            FinalResult AS Title,
            CreationDate
        FROM AuthenticationAttempt

        ORDER BY CreationDate DESC
        LIMIT ?;
    """

    return execute_query(query, (limit,))
