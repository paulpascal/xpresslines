"""Application factory: the composition root.

The only place where concrete choices are made (which fare policy, which
booking rules, which clock, who listens to events) and wired together.
Everything else receives its dependencies; nothing reaches for a global.
"""

import logging
import time
import uuid

from flask import g, request
from flask.json.provider import DefaultJSONProvider
from flask_openapi3 import Info, OpenAPI

from . import config
from .api import bp, register_error_handlers, validation_error_response
from .api.schemas import ErrorOut
from .cli import register_commands
from .domain.booking_rules import DEFAULT_BOOKING_RULES
from .domain.clock import system_clock
from .domain.events import ALL_EVENTS, EventBus, log_event
from .domain.pricing import ZoneFareTable
from .infra.db import make_session_factory
from .infra.logging_setup import configure_logging
from .services import Services

log = logging.getLogger("app.http")


def build_services() -> Services:
    events = EventBus()
    for event_type in ALL_EVENTS:
        events.subscribe(event_type, log_event)  # later: SMS, analytics, a job queue
    return Services(
        pricing=ZoneFareTable(),
        booking_rules=DEFAULT_BOOKING_RULES,
        clock=system_clock,
        events=events,
    )


def create_app(database_url: str | None = None, services: Services | None = None) -> OpenAPI:
    configure_logging()
    config.check()

    # OpenAPI is a Flask subclass that validates typed route parameters and
    # generates the docs (Swagger UI at /api/v1/docs/swagger).
    app = OpenAPI(
        __name__,
        info=Info(
            title="XpressLines booking API",
            version="1.0.0",
            description="Fares, trip search and seat booking for a Nigerian intercity bus operator. "
                        "Times are Lagos time (+01:00); money is a decimal string with its currency.",
        ),
        doc_prefix="/api/v1/docs",
        security_schemes={},
        validation_error_status=422,
        validation_error_model=ErrorOut,
        validation_error_callback=validation_error_response,
    )
    if isinstance(app.json, DefaultJSONProvider):
        app.json.sort_keys = False  # keep fields in the order the schemas define

    session_factory = make_session_factory(database_url or config.DATABASE_URL)
    app.extensions["session_factory"] = session_factory
    app.extensions["services"] = services or build_services()

    @app.before_request
    def open_session():
        g.db = session_factory()
        g.started = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

    @app.teardown_request
    def close_session(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()  # rolls back anything not committed

    @app.after_request
    def log_request(response):
        duration_ms = (time.perf_counter() - g.get("started", time.perf_counter())) * 1000
        response.headers["X-Request-ID"] = g.get("request_id", "")
        log.info("request", extra={"fields": {
            "method": request.method, "path": request.path,
            "status": response.status_code, "duration_ms": round(duration_ms, 1),
        }})
        return response

    register_error_handlers(app)
    app.register_api(bp)
    register_commands(app)
    return app
