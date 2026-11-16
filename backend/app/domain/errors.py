"""Domain errors. Each one knows its API code and HTTP status, so the API
layer can translate them in one place."""


class DomainError(Exception):
    code = "domain_error"
    http_status = 400

    def __init__(self, message: str, **details):
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidRequest(DomainError):
    code = "invalid_request"
    http_status = 422


class TownNotFound(DomainError):
    code = "town_not_found"
    http_status = 404


class TripNotFound(DomainError):
    code = "trip_not_found"
    http_status = 404


class BookingNotFound(DomainError):
    code = "booking_not_found"
    http_status = 404


class TripNotBookable(DomainError):
    code = "trip_not_bookable"
    http_status = 409


class NotEnoughSeats(DomainError):
    code = "not_enough_seats"
    http_status = 409


class InvalidTransition(DomainError):
    code = "invalid_status_transition"
    http_status = 409


class ServiceBusy(DomainError):
    code = "service_busy"
    http_status = 503


class IdempotencyConflict(DomainError):
    code = "idempotency_key_reused"
    http_status = 409
