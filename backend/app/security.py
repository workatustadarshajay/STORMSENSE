"""Security headers, request size limit and a per-user rate limit."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")


class SecurityHeaders(BaseHTTPMiddleware):
    def __init__(self, app, production: bool = False) -> None:  # noqa: ANN001
        super().__init__(app)
        self.production = production

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        resp = await call_next(request)
        resp.headers.update({
            "Content-Security-Policy": CSP, "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
            "Referrer-Policy": "same-origin", "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
        })
        if request.url.path.startswith("/api"):
            resp.headers["Cache-Control"] = "no-store"
        if self.production:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resp


class BodyLimit(BaseHTTPMiddleware):
    """Reject oversized bodies up front. Every endpoint takes a tiny JSON body, so the cap is small.

    ponytail: trusts Content-Length; a chunked upload is still bounded by the field length limits in the request models.
    """

    def __init__(self, app, max_bytes: int, upload_prefix: str = "/api/ingest/", upload_bytes: int = 3_000_000) -> None:  # noqa: ANN001
        super().__init__(app)
        self.max_bytes, self.upload_prefix, self.upload_bytes = max_bytes, upload_prefix, upload_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Your-own-data uploads carry whole CSV files; every other endpoint takes a small JSON body.
        cap = self.upload_bytes if request.url.path.startswith(self.upload_prefix) else self.max_bytes
        if int(request.headers.get("content-length") or 0) > cap:
            return JSONResponse({"detail": {"code": "too_large", "message": "That request is too large."}}, status_code=413)
        return await call_next(request)


class RateLimiter:
    """Sliding window per key. ponytail: in-process, which is right for a single app instance; use a shared store to scale out."""

    def __init__(self, max_calls: int, window_seconds: float = 60.0) -> None:
        self.max_calls, self.window = max_calls, window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now, q = time.monotonic(), self.hits[key]
        while q and q[0] <= now - self.window:
            q.popleft()
        if len(q) >= self.max_calls:
            return False
        q.append(now)
        return True
