"""One JSON object per log line, each carrying the request id when there is one.

Log shippers (CloudWatch, Loki, Datadog...) parse JSON without custom rules, and
the request id ties a booking event to its HTTP request. LOG_FORMAT=text gives
a readable line for local development.
"""

import json
import logging
import os
from datetime import UTC, datetime

from flask import g, has_request_context


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = g.get("request_id") if has_request_context() else None
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        line = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            **getattr(record, "fields", {}),
        }
        if record.exc_info:
            line["exception"] = self.formatException(record.exc_info)
        return json.dumps(line, default=str)


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields = " ".join(f"{k}={v}" for k, v in getattr(record, "fields", {}).items())
        text = f"{self.formatTime(record)} {record.levelname} {record.getMessage()} {fields}"
        if request_id := getattr(record, "request_id", None):
            text += f" request_id={request_id}"
        return text + (f"\n{self.formatException(record.exc_info)}" if record.exc_info else "")


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(TextFormatter() if os.environ.get("LOG_FORMAT") == "text" else JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
