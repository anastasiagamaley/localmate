from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt

from config import get_config

cfg = get_config()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, account_type: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=cfg.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "account_type": account_type,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=cfg.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, cfg.secret_key, algorithms=[cfg.algorithm])
        return payload
    except JWTError:
        return None
