from database.database_manager import execute_insert, execute_non_query, execute_query, execute_query_one


def create_person(first_name, second_name, third_name, last_name):
    query = """
        INSERT INTO Person
        (
            FirstName,
            SecondName,
            ThirdName,
            LastName,
            CreationDate,
            LastUpdatedDate,
            IsDeleted
        )
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), 0);
    """

    person_id = execute_insert(query, (first_name, second_name, third_name, last_name))

    if person_id:
        print(f"[DATABASE] Person created successfully: {person_id}")

    return person_id


def get_person_by_id(person_id):
    query = """
        SELECT
            PersonID,
            FirstName,
            SecondName,
            ThirdName,
            LastName,
            FirstName || ' ' || SecondName || ' ' || ThirdName || ' ' || LastName AS FullName,
            CreationDate,
            LastUpdatedDate,
            IsDeleted
        FROM Person
        WHERE PersonID = ?
          AND IsDeleted = 0;
    """

    return execute_query_one(query, (person_id,))


def get_all_people():
    query = """
        SELECT
            PersonID,
            FirstName,
            SecondName,
            ThirdName,
            LastName,
            FirstName || ' ' || SecondName || ' ' || ThirdName || ' ' || LastName AS FullName,
            CreationDate,
            LastUpdatedDate,
            IsDeleted
        FROM Person
        WHERE IsDeleted = 0
        ORDER BY PersonID DESC;
    """

    return execute_query(query)


def update_person(person_id, first_name, second_name, third_name, last_name):
    query = """
        UPDATE Person
        SET
            FirstName = ?,
            SecondName = ?,
            ThirdName = ?,
            LastName = ?,
            LastUpdatedDate = datetime('now')
        WHERE PersonID = ?
          AND IsDeleted = 0;
    """

    rows = execute_non_query(query, (first_name, second_name, third_name, last_name, person_id))

    if rows > 0:
        print(f"[DATABASE] Person updated successfully: {person_id}")

    return rows > 0


def soft_delete_person(person_id):
    query = """
        UPDATE Person
        SET
            IsDeleted = 1,
            LastUpdatedDate = datetime('now')
        WHERE PersonID = ?;
    """

    rows = execute_non_query(query, (person_id,))

    if rows > 0:
        print(f"[DATABASE] Person deleted successfully: {person_id}")

    return rows > 0
