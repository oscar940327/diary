import base64
import binascii
import json
from datetime import UTC, date, datetime
from typing import Annotated, Literal, TypedDict
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator

from diary_api.auth import (
    AuthenticatedIdentity,
    authentication_required,
    require_authenticated_identity,
)
from diary_api.config import cors_origins_from_environment
from diary_api.entries import (
    CalendarDayCount,
    EntryNotFound,
    EntryRecord,
    EntryRevisionRecord,
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


class ReplaceOriginalContentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_current_revision_id: UUID
    original_content: str

    @field_validator("original_content")
    @classmethod
    def original_content_cannot_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Original Content cannot be blank")
        return value


class RestoreEntryRevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_revision_id: UUID
    expected_current_revision_id: UUID


class ChangeEntryTimeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_at: datetime

    @field_validator("entry_at")
    @classmethod
    def entry_time_must_include_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Entry Time must include a UTC offset")
        return value.astimezone(UTC)


class EntryRevisionHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_id: UUID
    current_revision_id: UUID
    revisions: list[EntryRevisionRecord]


class EntryDateGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    entries: list[EntryRecord]


class CalendarDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    entry_count: int


class CalendarMonth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    month: str
    time_zone: Literal["Asia/Taipei"]
    days: list[CalendarDay]


class HistoryCursor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[2] = 2
    anchor_date: date
    direction: Literal["older", "newer"]
    entry_at: datetime
    entry_id: UUID
    snapshot: str


class HistoryPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor_date: date
    groups: list[EntryDateGroup]
    older_cursor: str | None
    newer_cursor: str | None


app = FastAPI(title="Diary API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(cors_origins_from_environment()),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
) -> AuthenticatedIdentity:
    try:
        owner_id = await registry.owner_id()
    except OwnerRegistryUnavailable as error:
        raise owner_authorization_service_unavailable() from error

    if identity.user_id != owner_id:
        raise authentication_required()

    return identity


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


def entry_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Entry not found",
    )


def invalid_history_cursor() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="History cursor is invalid",
    )


def encode_history_cursor(cursor: HistoryCursor) -> str:
    payload = cursor.model_dump_json().encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_history_cursor(value: str) -> HistoryCursor:
    try:
        padding = "=" * (-len(value) % 4)
        decoded = base64.b64decode(
            value + padding,
            altchars=b"-_",
            validate=True,
        )
        payload = json.loads(decoded)
        return HistoryCursor.model_validate(payload)
    except (
        binascii.Error,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        raise invalid_history_cursor() from error


def group_entries(entries: list[EntryRecord]) -> list[EntryDateGroup]:
    groups: list[EntryDateGroup] = []
    for entry in entries:
        if not groups or groups[-1].date != entry.owner_date:
            groups.append(
                EntryDateGroup(date=entry.owner_date, entries=[])
            )
        groups[-1].entries.append(entry)
    return groups


@app.get("/health")
def health() -> HealthResponse:
    return {
        "service": "diary-api",
        "status": "ready",
    }


@app.get("/auth/me")
def authenticated_owner(
    owner: AuthenticatedIdentity = Depends(require_owner),
) -> OwnerResponse:
    return {
        "status": "authenticated",
        "owner_id": str(owner.user_id),
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
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryRecord:
    try:
        entry, was_created = await store.create(
            access_token=owner.access_token,
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
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryDateGroup:
    owner_date = datetime.now(ZoneInfo("Asia/Taipei")).date()
    try:
        entries = await store.list_for_date(
            access_token=owner.access_token,
            owner_date=owner_date,
        )
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error
    return EntryDateGroup(date=owner_date, entries=entries)


@app.get(
    "/entries/calendar",
    response_model=CalendarMonth,
)
async def list_calendar_month(
    month: Annotated[
        str,
        Query(pattern=r"^\d{4}-(?:0[1-9]|1[0-2])$"),
    ],
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> CalendarMonth:
    try:
        month_start = date.fromisoformat(f"{month}-01")
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Calendar month is invalid",
        ) from error
    try:
        days: list[CalendarDayCount] = await store.list_calendar_month(
            access_token=owner.access_token,
            month=month_start,
        )
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error
    return CalendarMonth(
        month=month,
        time_zone="Asia/Taipei",
        days=[
            CalendarDay(
                date=day.owner_date,
                entry_count=day.entry_count,
            )
            for day in days
        ],
    )


@app.get(
    "/entries/history",
    response_model=HistoryPage,
)
async def list_history_entries(
    anchor_date: Annotated[date | None, Query()] = None,
    direction: Annotated[
        Literal["older", "newer"] | None,
        Query(),
    ] = None,
    cursor: Annotated[
        str | None,
        Query(min_length=1, max_length=2048),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> HistoryPage:
    owner_today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    if cursor is None:
        if direction is not None:
            raise invalid_history_cursor()
        resolved_anchor = anchor_date or owner_today
        resolved_direction: Literal[
            "initial",
            "older",
            "newer",
        ] = "initial"
        cursor_entry_at = None
        cursor_entry_id = None
        snapshot = None
    else:
        if direction is None or anchor_date is not None:
            raise invalid_history_cursor()
        decoded_cursor = decode_history_cursor(cursor)
        if decoded_cursor.direction != direction:
            raise invalid_history_cursor()
        resolved_anchor = decoded_cursor.anchor_date
        resolved_direction = direction
        cursor_entry_at = decoded_cursor.entry_at
        cursor_entry_id = decoded_cursor.entry_id
        snapshot = decoded_cursor.snapshot

    try:
        history = await store.list_history(
            access_token=owner.access_token,
            anchor_date=resolved_anchor,
            direction=resolved_direction,
            cursor_entry_at=cursor_entry_at,
            cursor_entry_id=cursor_entry_id,
            snapshot=snapshot,
            limit=limit,
        )
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error

    older_cursor = None
    newer_cursor = None
    if history.has_older:
        if (
            history.older_cursor_entry_at is None
            or history.older_cursor_entry_id is None
        ):
            raise entry_service_unavailable()
        older_cursor = encode_history_cursor(
            HistoryCursor(
                anchor_date=resolved_anchor,
                direction="older",
                entry_at=history.older_cursor_entry_at,
                entry_id=history.older_cursor_entry_id,
                snapshot=history.snapshot,
            )
        )
    if history.has_newer:
        if (
            history.newer_cursor_entry_at is None
            or history.newer_cursor_entry_id is None
        ):
            raise entry_service_unavailable()
        newer_cursor = encode_history_cursor(
            HistoryCursor(
                anchor_date=resolved_anchor,
                direction="newer",
                entry_at=history.newer_cursor_entry_at,
                entry_id=history.newer_cursor_entry_id,
                snapshot=history.snapshot,
            )
        )

    return HistoryPage(
        anchor_date=resolved_anchor,
        groups=group_entries(history.entries),
        older_cursor=older_cursor,
        newer_cursor=newer_cursor,
    )


@app.get(
    "/entries/{entry_id}",
    response_model=EntryRecord,
)
async def get_entry(
    entry_id: UUID,
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryRecord:
    try:
        return await store.get(
            access_token=owner.access_token,
            entry_id=entry_id,
        )
    except EntryNotFound as error:
        raise entry_not_found() from error
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error


@app.get(
    "/entries/{entry_id}/revisions",
    response_model=EntryRevisionHistory,
)
async def list_entry_revisions(
    entry_id: UUID,
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryRevisionHistory:
    try:
        revisions = await store.list_revisions(
            access_token=owner.access_token,
            entry_id=entry_id,
        )
    except EntryNotFound as error:
        raise entry_not_found() from error
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error
    current_revision = next(
        (revision for revision in revisions if revision.is_current),
        None,
    )
    if current_revision is None:
        raise entry_service_unavailable()
    return EntryRevisionHistory(
        entry_id=entry_id,
        current_revision_id=current_revision.id,
        revisions=revisions,
    )


@app.put(
    "/entries/{entry_id}/entry-time",
    response_model=EntryRecord,
)
async def change_entry_time(
    entry_id: UUID,
    request: ChangeEntryTimeRequest,
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryRecord:
    try:
        return await store.change_entry_time(
            access_token=owner.access_token,
            entry_id=entry_id,
            entry_at=request.entry_at,
        )
    except EntryNotFound as error:
        raise entry_not_found() from error
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error


@app.put(
    "/entries/{entry_id}/original-content",
    response_model=EntryRecord,
)
async def replace_entry_original_content(
    entry_id: UUID,
    request: ReplaceOriginalContentRequest,
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryRecord | JSONResponse:
    try:
        entry, edit_applied = await store.replace_original_content(
            access_token=owner.access_token,
            entry_id=entry_id,
            expected_current_revision_id=(
                request.expected_current_revision_id
            ),
            original_content=request.original_content,
        )
    except EntryNotFound as error:
        raise entry_not_found() from error
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error

    if not edit_applied:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": {
                    "code": "stale_entry_revision",
                    "message": (
                        "Original Content changed after this editor opened."
                    ),
                    "current_entry": entry.model_dump(mode="json"),
                }
            },
        )
    return entry


@app.post(
    "/entries/{entry_id}/revision-restorations",
    response_model=EntryRecord,
)
async def restore_entry_revision(
    entry_id: UUID,
    request: RestoreEntryRevisionRequest,
    owner: AuthenticatedIdentity = Depends(require_owner),
    store: SupabaseEntryStore = Depends(entry_store),
) -> EntryRecord | JSONResponse:
    try:
        entry, restore_applied = await store.restore_revision(
            access_token=owner.access_token,
            entry_id=entry_id,
            selected_revision_id=request.selected_revision_id,
            expected_current_revision_id=(
                request.expected_current_revision_id
            ),
        )
    except EntryNotFound as error:
        raise entry_not_found() from error
    except EntryStoreUnavailable as error:
        raise entry_service_unavailable() from error

    if not restore_applied:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": {
                    "code": "stale_entry_revision",
                    "message": (
                        "Original Content changed after this restore "
                        "was prepared."
                    ),
                    "current_entry": entry.model_dump(mode="json"),
                }
            },
        )
    return entry
