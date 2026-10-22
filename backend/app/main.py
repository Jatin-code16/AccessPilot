from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.scans import router as scans_router
from app.core.config import get_settings
from app.core.errors import AccessPilotError, accesspilot_error_handler, validation_error_content
from app.core.models import HealthResponse


settings = get_settings()
app = FastAPI(title="AccessPilot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)
app.add_exception_handler(AccessPilotError, accesspilot_error_handler)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, __: RequestValidationError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=422, content=validation_error_content([]))


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        browserAvailable=False,
        modelConfigured=settings.model_configured,
        modelName=settings.ai_model,
        engineVersion="unknown",
    )


app.include_router(scans_router)
