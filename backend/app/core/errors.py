from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AutoOpsError(Exception):
    """Base class for application-level errors that map to HTTP responses."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AutoOpsError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AutoOpsError):
    """Raised for invalid state transitions or duplicate/idempotent operations."""

    status_code = status.HTTP_409_CONFLICT


class ApprovalRequiredError(AutoOpsError):
    """Raised when a mutating action is blocked pending human approval."""

    status_code = status.HTTP_403_FORBIDDEN


class InvestigationFailedError(AutoOpsError):
    """Raised when the investigation provider fails to produce a diagnosis."""

    status_code = status.HTTP_502_BAD_GATEWAY


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AutoOpsError)
    async def autoops_error_handler(request: Request, exc: AutoOpsError) -> JSONResponse:
        logger.warning("request_failed", path=str(request.url), error=exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("validation_failed", path=str(request.url), errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=str(request.url), error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
