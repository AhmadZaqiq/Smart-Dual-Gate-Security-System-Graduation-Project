"""
Run database migrations for the mantrap SQLite database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database_manager import get_connection


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def table_has_column(connection, table_name, column_name):
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def audit_table_needs_migration():
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Audit'"
        )
        if cursor.fetchone() is None:
            return False

        return table_has_column(connection, "Audit", "Action")


def run_audit_migration():
    if not audit_table_needs_migration():
        print("[MIGRATION] Audit table already up to date", flush=True)
        return

    sql_path = MIGRATIONS_DIR / "001_fix_audit_table.sql"

    with open(sql_path, "r", encoding="utf-8") as sql_file:
        script = sql_file.read()

    with get_connection() as connection:
        connection.executescript(script)
        connection.commit()

    print("[MIGRATION] Audit table migrated successfully", flush=True)


def run_admin_role_migration():
    with get_connection() as connection:
        if table_has_column(connection, "AdminUser", "Role"):
            print("[MIGRATION] AdminUser.Role already exists", flush=True)
            return

    sql_path = MIGRATIONS_DIR / "002_add_admin_role.sql"

    with open(sql_path, "r", encoding="utf-8") as sql_file:
        script = sql_file.read()

    with get_connection() as connection:
        connection.executescript(script)
        connection.commit()

    print("[MIGRATION] AdminUser role column added", flush=True)


def run_all_migrations():
    run_audit_migration()
    run_admin_role_migration()
    print("[MIGRATION] All migrations completed", flush=True)


if __name__ == "__main__":
    run_all_migrations()
