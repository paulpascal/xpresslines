"""Every error leaves the API in one shape: {"error": {"code", "message", "details"}}."""

import logging

from flask import Flask, jsonify, make_response
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeout
from werkzeug.exceptions import HTTPException

from ..domain.errors import DomainError

log = logging.getLogger("app.http")


def error_response(status: int, code: str, message: str, details: dict | None = None):
    body = {"error": {"code": code, "message": message, "details": details or {}}}
    return make_response(jsonify(body), status)


def validation_error_response(error: ValidationError):
    details = [
        {"field": ".".join(str(part) for part in e["loc"]), "message": e["msg"]}
        for e in error.errors(include_url=False)
    ]
    return error_response(422, "validation_error", "The request is not valid", {"fields": details})


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def domain_error(error: DomainError):
        return error_response(error.http_status, error.code, error.message, error.details)

    app.register_error_handler(ValidationError, validation_error_response)

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        code = (error.name or "http_error").lower().replace(" ", "_")
        return error_response(error.code or 500, code, error.description or error.name)

    @app.errorhandler(OperationalError)
    @app.errorhandler(PoolTimeout)
    def database_unavailable(error: Exception):
        # Lock or statement timeout, database down, or no free connection:
        # a temporary condition, so 503 and let the client retry.
        log.warning("database_unavailable", extra={"fields": {"error": type(error).__name__}})
        return error_response(503, "service_busy", "The service is busy, please try again in a moment")

    @app.errorhandler(Exception)
    def unexpected_error(error: Exception):
        log.exception("unhandled_error")
        return error_response(500, "internal_error", "Something went wrong, please try again")
