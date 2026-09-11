from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from secrets import token_hex
from jose import jwt, JWTError
from app.core.config import settings

ALGORITHM = "HS256"
ITERATIONS = 210_000

def hash_password(password: str) -> str:
    salt = token_hex(16)
    digest = pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"

def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations, salt, expected = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return digest == expected
    except Exception:
        return False

def create_access_token(user_id, role):
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_token(token):
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
