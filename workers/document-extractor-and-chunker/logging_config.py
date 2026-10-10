import json
import logging
import logging.config
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone


request_id_context: ContextVar[str | None] = ContextVar(
    "request_id", default=None
)
job_id_context: ContextVar[str | None] = ContextVar("job_id", default=None)
attempt_context: ContextVar[int | None] = ContextVar("attempt", default=None)


@contextmanager
def bind_job_context(request_id: str, job_id: str, attempt: int):
    request_token = request_id_context.set(request_id)
    job_token = job_id_context.set(str(job_id))
    attempt_token = attempt_context.set(attempt)
    try:
        yield
    finally:
        attempt_context.reset(attempt_token)
        job_id_context.reset(job_token)
        request_id_context.reset(request_token)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
            "job_id": job_id_context.get(),
            "attempt": attempt_context.get(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack"] = self.formatStack(record.stack_info)
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": JsonFormatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {"level": "INFO", "handlers": ["console"]},
        }
    )
