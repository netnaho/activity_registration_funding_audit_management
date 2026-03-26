from datetime import datetime, timezone

import app.models  # noqa: F401
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def user_factory(db_session: Session):
    def _create(username: str, role: UserRole, password: str = "Pass@123456") -> User:
        user = User(
            username=username,
            full_name=username.title(),
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create
