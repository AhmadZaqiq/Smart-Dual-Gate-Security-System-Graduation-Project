import hashlib

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password, stored_hash):
    if not stored_hash:
        return False

    if stored_hash.startswith("pbkdf2:") or stored_hash.startswith("scrypt:"):
        return check_password_hash(stored_hash, password)

    legacy_hash = hashlib.sha256(password.encode()).hexdigest()
    return legacy_hash == stored_hash
