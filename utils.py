import bcrypt
def password_hash(password: str) -> bytes:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password


def verify_password(plain_password: str, stored_hash: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), stored_hash)