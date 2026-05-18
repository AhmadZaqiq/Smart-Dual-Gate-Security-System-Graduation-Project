import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "mantrap.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def row_to_dict(row):
    if row is None:
        return None

    return dict(row)


def rows_to_list(rows):
    return [dict(row) for row in rows]


def execute_query(query, params=()):
    try:
        with get_connection() as connection:
            cursor = connection.execute(query, params)
            return rows_to_list(cursor.fetchall())

    except Exception as error:
        print(f"[DATABASE] Query error: {error}")
        return []


def execute_query_one(query, params=()):
    try:
        with get_connection() as connection:
            cursor = connection.execute(query, params)
            return row_to_dict(cursor.fetchone())

    except Exception as error:
        print(f"[DATABASE] Query one error: {error}")
        return None


def execute_non_query(query, params=()):
    try:
        with get_connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
            return cursor.rowcount

    except Exception as error:
        print(f"[DATABASE] Non query error: {error}")
        return 0


def execute_insert(query, params=()):
    try:
        with get_connection() as connection:
            cursor = connection.execute(query, params)
            connection.commit()
            return cursor.lastrowid

    except Exception as error:
        print(f"[DATABASE] Insert error: {error}")
        return None
