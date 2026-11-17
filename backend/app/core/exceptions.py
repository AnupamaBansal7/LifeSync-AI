from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class LifeSyncException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, code: str = "BAD_REQUEST"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundException(LifeSyncException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            message=f"{resource} not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
        )


class PermissionDeniedException(LifeSyncException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
        )


class ApprovalRequiredException(LifeSyncException):
    def __init__(self, approval_id: str, summary: str):
        super().__init__(
            message=f"User approval required ({approval_id}): {summary}",
            status_code=status.HTTP_202_ACCEPTED,
            code="APPROVAL_REQUIRED",
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LifeSyncException)
    async def lifesync_exception_handler(request: Request, exc: LifeSyncException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                }
            },
        )