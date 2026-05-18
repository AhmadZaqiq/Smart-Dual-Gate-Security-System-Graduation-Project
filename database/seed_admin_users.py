import sys
from pathlib import Path
import hashlib

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "database"))

from employee_repository import add_person
from database_manager import execute_query


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


admins = [
    {
        "national_id": "211043",
        "first": "Ahmad",
        "second": "Yousef",
        "third": "Khalil",
        "last": "Zaqiq",
        "username": "ahmad",
        "email": "ahmad@mantrap.local",
        "password": "123456"
    },
    {
        "national_id": "217023",
        "first": "Diyaa",
        "second": "Taher",
        "third": "Mohammad",
        "last": "Etkedek",
        "username": "diyaa",
        "email": "diyaa@mantrap.local",
        "password": "123456"
    }
]


def add_admin_user(
    person_id,
    username,
    email,
    password
):
    execute_query("""
        INSERT INTO AdminUser (
            PersonID,
            UserName,
            Email,
            PasswordHash
        )
        VALUES (?, ?, ?, ?)
    """, (
        person_id,
        username,
        email,
        hash_password(password)
    ))


def seed_admins():
    for admin in admins:
        person_id = add_person(
            national_id=admin["national_id"],
            first_name=admin["first"],
            second_name=admin["second"],
            third_name=admin["third"],
            last_name=admin["last"]
        )

        add_admin_user(
            person_id=person_id,
            username=admin["username"],
            email=admin["email"],
            password=admin["password"]
        )

        print(
            f"[DATABASE] Admin added: "
            f"{admin['first']} "
            f"{admin['last']}"
        )

    print("[DATABASE] All admins added successfully")


if __name__ == "__main__":
    seed_admins()
