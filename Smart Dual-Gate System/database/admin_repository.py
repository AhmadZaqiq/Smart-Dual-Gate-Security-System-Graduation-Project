from database.database_manager import (
    execute_insert,
    execute_non_query,
    execute_query,
    execute_query_one
)


def create_admin_user(person_id, username, email, password_hash, is_active=1):
    query = """
        INSERT INTO AdminUser
        (
            PersonID,
            UserName,
            Email,
            PasswordHash,
            IsActive,
            IsDeleted,
            CreationDate,
            LastUpdatedDate
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            ?,
            0,
            datetime('now'),
            datetime('now')
        );
    """

    admin_id = execute_insert(
        query,
        (
            person_id,
            username,
            email,
            password_hash,
            is_active
        )
    )

    if admin_id:
        print(f"[DATABASE] Admin user created: {admin_id}", flush=True)

    return admin_id


def get_admin_by_id(admin_user_id):
    query = """
        SELECT
            A.AdminUserID,
            A.PersonID,
            A.UserName,
            A.Email,
            A.PasswordHash,
            A.IsActive,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName
        FROM AdminUser A
        INNER JOIN Person P
            ON P.PersonID = A.PersonID
        WHERE A.AdminUserID = ?
          AND A.IsDeleted = 0
          AND P.IsDeleted = 0;
    """

    return execute_query_one(query, (admin_user_id,))


def get_admin_by_username(username):
    query = """
        SELECT
            A.AdminUserID,
            A.PersonID,
            A.UserName,
            A.Email,
            A.PasswordHash,
            A.IsActive,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName
        FROM AdminUser A
        INNER JOIN Person P
            ON P.PersonID = A.PersonID
        WHERE A.UserName = ?
          AND A.IsDeleted = 0
          AND P.IsDeleted = 0;
    """

    return execute_query_one(query, (username,))


def get_admin_by_email(email):
    query = """
        SELECT
            A.AdminUserID,
            A.PersonID,
            A.UserName,
            A.Email,
            A.PasswordHash,
            A.IsActive,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName
        FROM AdminUser A
        INNER JOIN Person P
            ON P.PersonID = A.PersonID
        WHERE A.Email = ?
          AND A.IsDeleted = 0
          AND P.IsDeleted = 0;
    """

    return execute_query_one(query, (email,))


def get_all_admin_users():
    query = """
        SELECT
            A.AdminUserID,
            A.PersonID,
            A.UserName,
            A.Email,
            A.IsActive,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
            A.CreationDate,
            A.LastUpdatedDate
        FROM AdminUser A
        INNER JOIN Person P
            ON P.PersonID = A.PersonID
        WHERE A.IsDeleted = 0
          AND P.IsDeleted = 0
        ORDER BY A.AdminUserID DESC;
    """

    return execute_query(query)


def update_admin_user(admin_user_id, username, email, is_active):
    query = """
        UPDATE AdminUser
        SET
            UserName = ?,
            Email = ?,
            IsActive = ?,
            LastUpdatedDate = datetime('now')
        WHERE AdminUserID = ?
          AND IsDeleted = 0;
    """

    rows = execute_non_query(
        query,
        (
            username,
            email,
            is_active,
            admin_user_id
        )
    )

    if rows > 0:
        print(f"[DATABASE] Admin user updated: {admin_user_id}", flush=True)

    return rows > 0


def update_admin_password(admin_user_id, password_hash):
    query = """
        UPDATE AdminUser
        SET
            PasswordHash = ?,
            LastUpdatedDate = datetime('now')
        WHERE AdminUserID = ?
          AND IsDeleted = 0;
    """

    rows = execute_non_query(
        query,
        (
            password_hash,
            admin_user_id
        )
    )

    if rows > 0:
        print(f"[DATABASE] Admin password updated: {admin_user_id}", flush=True)

    return rows > 0


def set_admin_active_status(admin_user_id, is_active):
    query = """
        UPDATE AdminUser
        SET
            IsActive = ?,
            LastUpdatedDate = datetime('now')
        WHERE AdminUserID = ?
          AND IsDeleted = 0;
    """

    rows = execute_non_query(
        query,
        (
            is_active,
            admin_user_id
        )
    )

    if rows > 0:
        print(
            f"[DATABASE] Admin active status changed: {admin_user_id}",
            flush=True
        )

    return rows > 0


def activate_admin_user(admin_user_id):
    return set_admin_active_status(admin_user_id, 1)


def deactivate_admin_user(admin_user_id):
    return set_admin_active_status(admin_user_id, 0)


def soft_delete_admin_user(admin_user_id):
    query = """
        UPDATE AdminUser
        SET
            IsDeleted = 1,
            LastUpdatedDate = datetime('now')
        WHERE AdminUserID = ?;
    """

    rows = execute_non_query(query, (admin_user_id,))

    if rows > 0:
        print(f"[DATABASE] Admin user deleted: {admin_user_id}", flush=True)

    return rows > 0
