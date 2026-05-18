from database.database_manager import execute_insert, execute_query


def create_audit(admin_user_id, action_type, table_name=None, record_id=None, old_value=None, new_value=None, description=None):
    query = """
        INSERT INTO Audit
        (
            AdminUserID,
            ActionType,
            TableName,
            RecordID,
            OldValue,
            NewValue,
            Description,
            CreationDate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'));
    """

    audit_id = execute_insert(
        query,
        (
            admin_user_id,
            action_type,
            table_name,
            record_id,
            old_value,
            new_value,
            description
        )
    )

    if audit_id:
        print(f"[DATABASE] Audit saved: {audit_id}")

    return audit_id


def get_recent_audits(limit=50):
    query = """
        SELECT
            AU.AuditID,
            AU.AdminUserID,
            AD.UserName,
            P.FirstName || ' ' || P.SecondName || ' ' || P.ThirdName || ' ' || P.LastName AS AdminName,
            AU.ActionType,
            AU.TableName,
            AU.RecordID,
            AU.OldValue,
            AU.NewValue,
            AU.Description,
            AU.CreationDate
        FROM Audit AU
        LEFT JOIN AdminUser AD ON AD.AdminUserID = AU.AdminUserID
        LEFT JOIN Person P ON P.PersonID = AD.PersonID
        ORDER BY AU.AuditID DESC
        LIMIT ?;
    """

    return execute_query(query, (limit,))


def get_audits_by_admin(admin_user_id, limit=50):
    query = """
        SELECT
            AuditID,
            AdminUserID,
            ActionType,
            TableName,
            RecordID,
            OldValue,
            NewValue,
            Description,
            CreationDate
        FROM Audit
        WHERE AdminUserID = ?
        ORDER BY AuditID DESC
        LIMIT ?;
    """

    return execute_query(query, (admin_user_id, limit))


def get_audits_by_table(table_name, limit=50):
    query = """
        SELECT
            AuditID,
            AdminUserID,
            ActionType,
            TableName,
            RecordID,
            OldValue,
            NewValue,
            Description,
            CreationDate
        FROM Audit
        WHERE TableName = ?
        ORDER BY AuditID DESC
        LIMIT ?;
    """

    return execute_query(query, (table_name, limit))
