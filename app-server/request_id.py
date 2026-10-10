import logging
import time
import uuid
from contextvars import ContextVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_HEADER = b"x-request-id"
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)

logger = logging.getLogger(__name__)


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = next(
            (
                value.decode("latin-1")
                for name, value in scope["headers"]
                if name.lower() == REQUEST_ID_HEADER
            ),
            "",
        ) or str(uuid.uuid4())
        token = request_id_context.set(request_id)
        started_at = time.perf_counter()
        status_code = None

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != REQUEST_ID_HEADER
                ]
                headers.append((REQUEST_ID_HEADER, request_id.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
            logger.info(
                "Request completed",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                },
            )
        except Exception:
            logger.exception(
                "Request failed",
                extra={"method": scope["method"], "path": scope["path"]},
            )
            raise
        finally:
            request_id_context.reset(token)
