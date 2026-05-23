from database.database_manager import (
    execute_insert,
    execute_non_query,
    execute_query,
    execute_query_one
)


def create_employee(employee_number, person_id, is_active=1):
    query = """
        INSERT INTO Employee
        (
            EmployeeNumber,
            PersonID,
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
            0,
            datetime('now'),
            datetime('now')
        );
    """

    employee_id = execute_insert(
        query,
        (employee_number, person_id, is_active)
    )

    if employee_id:
        print(f"[DATABASE] Employee created: {employee_id}", flush=True)

    return employee_id


def get_employee_by_id(employee_id):
    query = """
        SELECT
            E.EmployeeID,
            E.EmployeeNumber,
            E.PersonID,
            P.FirstName,
            P.SecondName,
            P.ThirdName,
            P.LastName,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
            E.IsActive,
            E.IsDeleted,
            E.CreationDate,
            E.LastUpdatedDate
        FROM Employee E
        INNER JOIN Person P
            ON P.PersonID = E.PersonID
        WHERE E.EmployeeID = ?
          AND E.IsDeleted = 0
          AND P.IsDeleted = 0;
    """

    return execute_query_one(query, (employee_id,))


def get_employee_by_number(employee_number):
    query = """
        SELECT
            E.EmployeeID,
            E.EmployeeNumber,
            E.PersonID,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
            E.IsActive
        FROM Employee E
        INNER JOIN Person P
            ON P.PersonID = E.PersonID
        WHERE E.EmployeeNumber = ?
          AND E.IsDeleted = 0
          AND P.IsDeleted = 0;
    """

    return execute_query_one(query, (employee_number,))


def get_all_employees():
    query = """
        SELECT
            E.EmployeeID,
            E.EmployeeNumber,
            E.PersonID,
            P.FirstName,
            P.SecondName,
            P.ThirdName,
            P.LastName,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
            E.IsActive,
            EA.RFIDUID,
            EA.FingerprintPosition,
            EA.FaceImagePath,
            E.CreationDate,
            E.LastUpdatedDate
        FROM Employee E
        INNER JOIN Person P
            ON P.PersonID = E.PersonID
        LEFT JOIN EmployeeAuthentication EA
            ON EA.EmployeeID = E.EmployeeID
        WHERE E.IsDeleted = 0
          AND P.IsDeleted = 0
        ORDER BY E.EmployeeID DESC;
    """

    return execute_query(query)


def search_employees(search_text):
    query = """
        SELECT
            E.EmployeeID,
            E.EmployeeNumber,
            P.FirstName || ' ' || P.SecondName || ' ' ||
            P.ThirdName || ' ' || P.LastName AS FullName,
            E.IsActive
        FROM Employee E
        INNER JOIN Person P
            ON P.PersonID = E.PersonID
        WHERE E.IsDeleted = 0
          AND P.IsDeleted = 0
          AND
          (
                E.EmployeeNumber LIKE ?
             OR P.FirstName LIKE ?
             OR P.SecondName LIKE ?
             OR P.ThirdName LIKE ?
             OR P.LastName LIKE ?
          )
        ORDER BY E.EmployeeID DESC;
    """

    value = f"%{search_text}%"

    return execute_query(
        query,
        (value, value, value, value, value)
    )


def update_employee(employee_id, employee_number, is_active):
    query = """
        UPDATE Employee
        SET
            EmployeeNumber = ?,
            IsActive = ?,
            LastUpdatedDate = datetime('now')
        WHERE EmployeeID = ?
          AND IsDeleted = 0;
    """

    rows = execute_non_query(
        query,
        (employee_number, is_active, employee_id)
    )

    if rows > 0:
        print(f"[DATABASE] Employee updated: {employee_id}", flush=True)

    return rows > 0


def set_employee_active_status(employee_id, is_active):
    query = """
        UPDATE Employee
        SET
            IsActive = ?,
            LastUpdatedDate = datetime('now')
        WHERE EmployeeID = ?
          AND IsDeleted = 0;
    """

    rows = execute_non_query(
        query,
        (is_active, employee_id)
    )

    if rows > 0:
        print(
            f"[DATABASE] Employee active status changed: {employee_id}",
            flush=True
        )

    return rows > 0


def activate_employee(employee_id):
    return set_employee_active_status(employee_id, 1)


def deactivate_employee(employee_id):
    return set_employee_active_status(employee_id, 0)


def soft_delete_employee(employee_id):
    query = """
        UPDATE Employee
        SET
            IsDeleted = 1,
            LastUpdatedDate = datetime('now')
        WHERE EmployeeID = ?;
    """

    rows = execute_non_query(query, (employee_id,))

    if rows > 0:
        print(f"[DATABASE] Employee deleted: {employee_id}", flush=True)

    return rows > 0
