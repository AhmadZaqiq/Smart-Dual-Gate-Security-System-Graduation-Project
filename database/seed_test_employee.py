import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "database"))

from employee_repository import (
    add_person,
    add_employee,
    add_employee_authentication
)


employees = [
    {
        "national_id": "211001",
        "first": "Ahmad",
        "second": "Yousef",
        "third": "Khalil",
        "last": "Zaqiq",
        "employee_number": "EMP-0001",
        "rfid": "682511166205",
        "finger": 0,
    },
    {
        "national_id": "211002",
        "first": "Mohammad",
        "second": "Saleh",
        "third": "Ali",
        "last": "Nasser",
        "employee_number": "EMP-0002",
        "rfid": "100000000002",
        "finger": 1,
    },
    {
        "national_id": "211003",
        "first": "Omar",
        "second": "Ibrahim",
        "third": "Hassan",
        "last": "Darwish",
        "employee_number": "EMP-0003",
        "rfid": "100000000003",
        "finger": 2,
    },
    {
        "national_id": "211004",
        "first": "Yazan",
        "second": "Mahmoud",
        "third": "Khaled",
        "last": "Hamdan",
        "employee_number": "EMP-0004",
        "rfid": "100000000004",
        "finger": 3,
    },
    {
        "national_id": "211005",
        "first": "Laith",
        "second": "Fadi",
        "third": "Samir",
        "last": "Qasim",
        "employee_number": "EMP-0005",
        "rfid": "100000000005",
        "finger": 4,
    },
    {
        "national_id": "211006",
        "first": "Karam",
        "second": "Adel",
        "third": "Nidal",
        "last": "Sabbah",
        "employee_number": "EMP-0006",
        "rfid": "100000000006",
        "finger": 5,
    },
    {
        "national_id": "211007",
        "first": "Saeed",
        "second": "Rami",
        "third": "Bassam",
        "last": "Tawil",
        "employee_number": "EMP-0007",
        "rfid": "100000000007",
        "finger": 6,
    },
    {
        "national_id": "211008",
        "first": "Anas",
        "second": "Jamal",
        "third": "Raed",
        "last": "Shahin",
        "employee_number": "EMP-0008",
        "rfid": "100000000008",
        "finger": 7,
    },
    {
        "national_id": "211009",
        "first": "Tariq",
        "second": "Naeem",
        "third": "Ziad",
        "last": "Masri",
        "employee_number": "EMP-0009",
        "rfid": "100000000009",
        "finger": 8,
    },
    {
        "national_id": "211010",
        "first": "Fares",
        "second": "Wael",
        "third": "Hatem",
        "last": "Khoury",
        "employee_number": "EMP-0010",
        "rfid": "100000000010",
        "finger": 9,
    }
]


def seed_employees():
    for employee in employees:
        person_id = add_person(
            national_id=employee["national_id"],
            first_name=employee["first"],
            second_name=employee["second"],
            third_name=employee["third"],
            last_name=employee["last"],
            picture="auth/face_data/reference_face.jpg"
        )

        employee_id = add_employee(
            person_id=person_id,
            employee_number=employee["employee_number"]
        )

        add_employee_authentication(
            employee_id=employee_id,
            rfid_uid=employee["rfid"],
            fingerprint_position=employee["finger"],
            face_image_path="auth/face_data/reference_face.jpg"
        )

        print(
            f"[DATABASE] Added: "
            f"{employee['first']} "
            f"{employee['last']}"
        )

    print("[DATABASE] All employees added successfully")


if __name__ == "__main__":
    seed_employees()
