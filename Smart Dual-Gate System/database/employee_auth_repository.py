from database.database_manager import (
    execute_insert,
    execute_non_query,
    execute_query_one
)


def create_employee_authentication(employee_id,
                                   rfid_uid=None,
                                   fingerprint_position=None,
                                   face_image_path=None):
    query = """
        INSERT INTO EmployeeAuthentication
        (
            EmployeeID,
            RFIDUID,
            FingerprintPosition,
            FaceImagePath,
            CreationDate,
            LastUpdatedDate
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            datetime('now'),
            datetime('now')
        );
    """

    auth_id = execute_insert(
        query,
        (
            employee_id,
            rfid_uid,
            fingerprint_position,
            face_image_path
        )
    )

    if auth_id:
        print(
            f"[DATABASE] Employee authentication created: {auth_id}",
            flush=True
        )

    return auth_id


def get_authentication_by_employee_id(employee_id):
    query = """
        SELECT
            EmployeeAuthenticationID,
            EmployeeID,
            RFIDUID,
            FingerprintPosition,
            FaceImagePath,
            CreationDate,
            LastUpdatedDate
        FROM EmployeeAuthentication
        WHERE EmployeeID = ?;
    """

    return execute_query_one(query, (employee_id,))


def get_employee_by_rfid_uid(rfid_uid):
    query = """
        SELECT
            E.EmployeeID,
            E.EmployeeNumber,
            E.IsActive,
            EA.RFIDUID,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName
        FROM EmployeeAuthentication EA
        INNER JOIN Employee E
            ON E.EmployeeID = EA.EmployeeID
        INNER JOIN Person P
            ON P.PersonID = E.PersonID
        WHERE EA.RFIDUID = ?
          AND E.IsActive = 1
          AND E.IsDeleted = 0
          AND P.IsDeleted = 0;
    """

    return execute_query_one(query, (str(rfid_uid),))


def get_employee_by_fingerprint_position(fingerprint_position):
    query = """
        SELECT
            E.EmployeeID,
            E.EmployeeNumber,
            E.IsActive,
            EA.FingerprintPosition,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName
        FROM EmployeeAuthentication EA
        INNER JOIN Employee E
            ON E.EmployeeID = EA.EmployeeID
        INNER JOIN Person P
            ON P.PersonID = E.PersonID
        WHERE EA.FingerprintPosition = ?
          AND E.IsActive = 1
          AND E.IsDeleted = 0
          AND P.IsDeleted = 0;
    """

    return execute_query_one(query, (fingerprint_position,))


def update_rfid_uid(employee_id, rfid_uid):
    query = """
        UPDATE EmployeeAuthentication
        SET
            RFIDUID = ?,
            LastUpdatedDate = datetime('now')
        WHERE EmployeeID = ?;
    """

    rows = execute_non_query(
        query,
        (str(rfid_uid), employee_id)
    )

    if rows > 0:
        print(
            f"[DATABASE] RFID UID updated for employee: {employee_id}",
            flush=True
        )

    return rows > 0


def update_fingerprint_position(employee_id, fingerprint_position):
    query = """
        UPDATE EmployeeAuthentication
        SET
            FingerprintPosition = ?,
            LastUpdatedDate = datetime('now')
        WHERE EmployeeID = ?;
    """

    rows = execute_non_query(
        query,
        (fingerprint_position, employee_id)
    )

    if rows > 0:
        print(
            f"[DATABASE] Fingerprint position updated for employee: "
            f"{employee_id}",
            flush=True
        )

    return rows > 0


def update_face_image_path(employee_id, face_image_path):
    query = """
        UPDATE EmployeeAuthentication
        SET
            FaceImagePath = ?,
            LastUpdatedDate = datetime('now')
        WHERE EmployeeID = ?;
    """

    rows = execute_non_query(
        query,
        (face_image_path, employee_id)
    )

    if rows > 0:
        print(
            f"[DATABASE] Face image path updated for employee: "
            f"{employee_id}",
            flush=True
        )

    return rows > 0


def delete_employee_authentication(employee_id):
    query = """
        DELETE FROM EmployeeAuthentication
        WHERE EmployeeID = ?;
    """

    rows = execute_non_query(query, (employee_id,))

    if rows > 0:
        print(
            f"[DATABASE] Employee authentication deleted: {employee_id}",
            flush=True
        )

    return rows > 0
