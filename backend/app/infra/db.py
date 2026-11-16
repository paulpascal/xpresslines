"""Database engine and sessions, with timeouts so a stuck lock fails fast."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .. import config


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_timeout=config.DB_POOL_TIMEOUT_S,
        connect_args={"options": (
            f"-c lock_timeout={config.DB_LOCK_TIMEOUT_MS} "
            f"-c statement_timeout={config.DB_STATEMENT_TIMEOUT_MS}"
        )},
    )
    # expire_on_commit=False: objects stay readable after commit, so the API
    # can serialise what a service returned without another query.
    return sessionmaker(engine, expire_on_commit=False)


@contextmanager
def committing(session: Session) -> Iterator[None]:
    """Commit on success, roll back on any error. Every write goes through this."""
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
