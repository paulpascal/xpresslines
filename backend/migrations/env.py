from alembic import context
from sqlalchemy import create_engine

from app import config
from app.domain.models import Base

target_metadata = Base.metadata


def database_url() -> str:
    # Tests pass their own URL; otherwise use the app's configuration.
    return context.config.attributes.get("database_url") or config.DATABASE_URL


def run_migrations_offline() -> None:
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
