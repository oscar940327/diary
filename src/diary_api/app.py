from typing import Literal, TypedDict

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from diary_api.auth import (
    AuthenticatedIdentity,
    authentication_required,
    require_authenticated_identity,
)
from diary_api.config import cors_origins_from_environment
from diary_api.owner_registry import (
    OwnerRegistryUnavailable,
    SupabaseOwnerRegistry,
    owner_registry,
)


class HealthResponse(TypedDict):
    service: Literal["diary-api"]
    status: Literal["ready"]


class OwnerResponse(TypedDict):
    status: Literal["authenticated"]
    owner_id: str


app = FastAPI(title="Diary API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(cors_origins_from_environment()),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "X-Idempotency-Key",
    ],
)


async def require_owner(
    identity: AuthenticatedIdentity = Depends(
        require_authenticated_identity
    ),
    registry: SupabaseOwnerRegistry = Depends(owner_registry),
) -> str:
    try:
        owner_id = await registry.owner_id()
    except OwnerRegistryUnavailable as error:
        raise owner_authorization_service_unavailable() from error

    if identity.user_id != owner_id:
        raise authentication_required()

    return str(identity.user_id)


def owner_authorization_service_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Owner authorization service unavailable",
    )


@app.get("/health")
def health() -> HealthResponse:
    return {
        "service": "diary-api",
        "status": "ready",
    }


@app.get("/auth/me")
def authenticated_owner(
    owner_id: str = Depends(require_owner),
) -> OwnerResponse:
    return {
        "status": "authenticated",
        "owner_id": owner_id,
    }
