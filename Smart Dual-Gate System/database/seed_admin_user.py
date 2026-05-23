"""
Create dashboard admin accounts for Ahmad and Diaa.
Passwords must be provided via environment variables only.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from database.admin_repository import create_admin_user, get_admin_by_username, update_admin_password
from database.database_manager import execute_non_query
from database.person_repository import create_person
from web_dashboard.auth.password_utils import hash_password

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ADMIN_ACCOUNTS = [
    {
        "username": "ahmad",
        "display_first": "Ahmad",
        "display_second": "Security",
        "display_third": "Super",
        "display_last": "Admin",
        "email": "ahmad@mantrap.local",
        "password_env": "AHMAD_ADMIN_PASSWORD",
        "role": "Super Admin",
    },
    {
        "username": "diaa",
        "display_first": "Diaa",
        "display_second": "Security",
        "display_third": "Control",
        "display_last": "Operator",
        "email": "diaa@mantrap.local",
        "password_env": "DIAA_ADMIN_PASSWORD",
        "role": "Operator",
    },
]

DEV_FALLBACK_PASSWORD = os.environ.get("DEV_ADMIN_FALLBACK_PASSWORD")


def _resolve_password(env_key):
    password = os.environ.get(env_key)

    if password:
        return password

    if DEV_FALLBACK_PASSWORD:
        print(
            f"[SEED] Warning: {env_key} missing. Using DEV_ADMIN_FALLBACK_PASSWORD for development only.",
            flush=True,
        )
        return DEV_FALLBACK_PASSWORD

    return None


def seed_admin_account(account):
    username = account["username"]
    password = _resolve_password(account["password_env"])

    if not password:
        print(
            f"[SEED] Skipped '{username}': set {account['password_env']} in .env before seeding.",
            flush=True,
        )
        return False

    password_hash = hash_password(password)
    existing = get_admin_by_username(username)

    if existing:
        update_admin_password(existing["AdminUserID"], password_hash)
        execute_non_query(
            "UPDATE AdminUser SET Role = ? WHERE AdminUserID = ?;",
            (account["role"], existing["AdminUserID"]),
        )
        print(f"[SEED] Admin '{username}' password hash refreshed.", flush=True)
        return True

    person_id = create_person(
        account["display_first"],
        account["display_second"],
        account["display_third"],
        account["display_last"],
    )

    if not person_id:
        print(f"[SEED] Failed to create person for '{username}'.", flush=True)
        return False

    admin_id = create_admin_user(
        person_id=person_id,
        username=username,
        email=account["email"],
        password_hash=password_hash,
    )

    if admin_id:
        execute_non_query(
            "UPDATE AdminUser SET Role = ? WHERE AdminUserID = ?;",
            (account["role"], admin_id),
        )
        print(f"[SEED] Admin '{username}' created successfully.", flush=True)
        return True

    return False


def seed_all_admins():
    print("[SEED] Seeding dashboard admin accounts...", flush=True)

    if not os.environ.get("AHMAD_ADMIN_PASSWORD") or not os.environ.get("DIAA_ADMIN_PASSWORD"):
        print(
            "[SEED] Warning: AHMAD_ADMIN_PASSWORD and/or DIAA_ADMIN_PASSWORD are not set.",
            flush=True,
        )
        print(
            "[SEED] Add them to .env, or set DEV_ADMIN_FALLBACK_PASSWORD for local development.",
            flush=True,
        )

    results = [seed_admin_account(account) for account in ADMIN_ACCOUNTS]

    if any(results):
        print("[SEED] Admin seeding completed.", flush=True)
    else:
        print("[SEED] No admin accounts were seeded.", flush=True)


if __name__ == "__main__":
    seed_all_admins()
