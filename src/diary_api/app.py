from datetime import UTC, date, datetime
from typing import Annotated, Literal, TypedDict
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, field_validator

from diary_api.auth import (
    AuthenticatedIdentity,
    authentication_required,
    require_authenticated_identity,
)
from diary_api.config import cors_origins_from_environment
from diary_api.entries import (
    EntryRecord,
    EntryStoreUnavailable,
    SupabaseEntryStore,
    entry_store,
)
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


class CreateEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_content: str
    entry_at: datetime | None = None

    @field_validator("original_content")
    @classmethod
    def original_content_cannot_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Original Content cannot be blank")
        return value

    @field_validator("entry_at")
    @classmethod
    def entry_time_must_include_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Entry Time must include a UTC offset")
        return value.astimezone(UTC)


class EntryDateGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    entries: list[EntryRecord]


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


def entry_service_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Entry service unavailable",
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


@app.post(
    "/entries",
    response_model=EntryRecord,
    status_code=status.HTTP_201_CREATED,
)
async def create_entry(
    request: CreateEntryRequest,
    response: Response,
    idempotency_key: Annotated[
        str,
        Header(
            alias="X-Idempotency-Key",
            min_length=1,
            max_length=200,
            pattern=r".*\S.*",
        ),
    ],
    owner_id: str = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryRecord:
    try:
        entry, was_created = await store.create(
            owner_id=UUID(owner_id),
            original_content=request.original_content,
            entry_at=request.entry_at,
            idempotency_key=idempotency_key,
        )
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error

    if not was_created:
        response.status_code = status.HTTP_200_OK
    return entry


@app.get(
    "/entries/today",
    response_model=EntryDateGroup,
)
async def list_today_entries(
    owner_id: str = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryDateGroup:
    owner_date = datetime.now(ZoneInfo("Asia/Taipei")).date()
    try:
        entries = await store.list_for_date(
            owner_id=UUID(owner_id),
            owner_date=owner_date,
        )
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error
    return EntryDateGroup(date=owner_date, entries=entries)
