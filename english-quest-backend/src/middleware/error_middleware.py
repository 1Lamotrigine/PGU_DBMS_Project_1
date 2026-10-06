import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("english_quest")


def _error_response(status_code: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or []}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            location = ".".join(str(part) for part in err.get("loc", []) if part != "body")
            details.append({"field": location, "message": err.get("msg", "invalid")})
        return _error_response(422, "VALIDATION_ERROR", "Request validation failed", details)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            return _error_response(
                exc.status_code,
                detail.get("code", "HTTP_ERROR"),
                detail.get("message", str(detail)),
                detail.get("details", []),
            )
        return _error_response(exc.status_code, "HTTP_ERROR", str(detail))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
