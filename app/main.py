"""
app/main.py
FastAPI application entry point.
Runs on port 4000 via: uvicorn app.main:app --host 0.0.0.0 --port 4000
Swagger UI: http://localhost:4000/docs
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import post_to_all_platforms

app = FastAPI(
    title="Automated Multi-Platform Posting System",
    description=(
        "A production-ready API that concurrently publishes messages to "
        "5 public platforms: Telegraph, Dpaste, Ntfy.sh, GitHub Gist, and HuggingFace."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Custom 422 validation error handler — clean, human-readable errors
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append(
            {
                "field": field or "request",
                "message": error["msg"],
                "type": error["type"],
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "detail": "Validation failed",
            "errors": errors,
        },
    )


# ---------------------------------------------------------------------------
# POST /posting — single endpoint
# ---------------------------------------------------------------------------
@app.post(
    "/posting",
    response_model=PostingResponse,
    summary="Post message to all platforms",
    description=(
        "Accepts a message with exactly one CTA link (≤200 chars) and "
        "concurrently publishes it to Telegraph, Dpaste, Ntfy.sh, GitHub Gist, "
        "and HuggingFace. Platform selection is handled internally."
    ),
    tags=["Posting"],
    status_code=200,
)
async def post_message(payload: PostingRequest) -> PostingResponse:
    results = await post_to_all_platforms(payload.message)
    return PostingResponse(success=True, results=results)
