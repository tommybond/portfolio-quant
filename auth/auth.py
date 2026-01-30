"""Authentication manager for user login and registration."""

from typing import Optional
from sqlalchemy.orm import Session

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def _hash_password(password: str) -> str:
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return password


def _verify_password(password: str, password_hash: str) -> bool:
    if BCRYPT_AVAILABLE:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    return password == password_hash


class AuthManager:
    def __init__(self, db: Optional[Session] = None):
        if db is None:
            from database.models import create_session
            self._session = create_session()
            self._own_session = True
        else:
            self._session = db
            self._own_session = False

    def _db(self) -> Session:
        return self._session

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: str = "user",
    ):
        from database.models import User
        existing = self._db().query(User).filter(User.username == username).first()
        if existing:
            return None
        user = User(
            username=username,
            email=email,
            password_hash=_hash_password(password),
            full_name=full_name or username,
            role=role,
            is_active=True,
        )
        self._db().add(user)
        self._db().commit()
        self._db().refresh(user)
        return user

    def authenticate(self, username: str, password: str):
        from database.models import User
        user = self._db().query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            return None
        if not _verify_password(password, user.password_hash):
            return None
        return user

    def __del__(self):
        if getattr(self, "_own_session", False) and getattr(self, "_session", None):
            try:
                self._session.close()
            except Exception:
                pass
