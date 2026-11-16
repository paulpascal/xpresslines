"""HTTP adapter: the only layer that knows about Flask requests and responses."""

from .errors import register_error_handlers, validation_error_response
from .routes import bp

__all__ = ["bp", "register_error_handlers", "validation_error_response"]
