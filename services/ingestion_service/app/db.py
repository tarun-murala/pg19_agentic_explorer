from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.engine import URL
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings


settings = get_settings()

_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

db_engine = create_engine(settings.database_url, connect_args=_connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(db_engine)


@contextmanager
def get_session() -> Iterator[Session]:
    session = Session(db_engine)
    try:
        yield session
    finally:
        session.close()
