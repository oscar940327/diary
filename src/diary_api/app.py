from typing import Literal, TypedDict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from diary_api.auth import (
    AuthenticatedIdentity,
    auth_settings,
    authentication_required,
    require_authenticated_identity,
)
from diary_api.config import AuthSettings, cors_origins_from_environment


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
    settings: AuthSettings = Depends(auth_settings),
) -> str:
    if identity.user_id != settings.owner_id:
        raise authentication_required()

    return str(identity.user_id)


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
