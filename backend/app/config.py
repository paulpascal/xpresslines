import os
from zoneinfo import ZoneInfo

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://bus:bus@localhost:55432/bus"
)

# Scaling knobs: connections each API process may hold.
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "5"))
THREADS = int(os.environ.get("THREADS", "4"))  # gunicorn threads per process

# Fail fast instead of queueing forever: a stuck lock or a slow query turns
# into a 503 "busy, retry" (safe, thanks to the Idempotency-Key).
DB_LOCK_TIMEOUT_MS = int(os.environ.get("DB_LOCK_TIMEOUT_MS", "2000"))
DB_STATEMENT_TIMEOUT_MS = int(os.environ.get("DB_STATEMENT_TIMEOUT_MS", "5000"))
DB_POOL_TIMEOUT_S = int(os.environ.get("DB_POOL_TIMEOUT_S", "5"))

# The operator sells and runs trips on Nigerian time. The database stores UTC;
# we convert at the edges (search by local date, display local times).
OPERATOR_TZ = ZoneInfo("Africa/Lagos")


def check() -> None:
    """Refuse to start with settings that would make requests wait for a connection."""
    if THREADS > DB_POOL_SIZE + DB_MAX_OVERFLOW:
        raise RuntimeError(
            f"THREADS={THREADS} is more than DB_POOL_SIZE + DB_MAX_OVERFLOW "
            f"({DB_POOL_SIZE} + {DB_MAX_OVERFLOW}): some requests would wait for a "
            "database connection. Raise the pool or lower THREADS."
        )
