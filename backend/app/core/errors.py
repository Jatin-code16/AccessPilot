from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class AccessPilotError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def accesspilot_error_handler(_: Request, error: AccessPilotError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(error=ErrorBody(code=error.code, message=error.message)).model_dump(by_alias=True),
    )


def validation_error_content(errors: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    return {"error": {"code": "invalid_request", "message": "Request validation failed."}}
