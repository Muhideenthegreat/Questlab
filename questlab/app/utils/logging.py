"""Logging helpers for structured JSON logging and request context."""

import json
import logging
from datetime import datetime, timezone
from flask import has_request_context, request, g


class RequestContextFilter(logging.Filter):
    """Inject request-specific fields into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if has_request_context():
            record.ip = request.remote_addr or "unknown"
            record.user_agent = (request.user_agent.string or "").replace("\n", " ")
            record.method = request.method
            record.path = request.path
            record.req_id = getattr(g, "request_id", None)
        else:
            record.ip = None
            record.user_agent = None
            record.method = None
            record.path = None
            record.req_id = None
        return True


class JSONLogFormatter(logging.Formatter):
    """Format logs as single-line JSON for easier ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "ip": getattr(record, "ip", None),
            "user_agent": getattr(record, "user_agent", None),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "req_id": getattr(record, "req_id", None),
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)
