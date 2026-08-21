from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from typing import Any, Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict

from diary_api.config import EntryStoreSettings


class EntryStoreUnavailable(Exception):
    pass


class EntryNotFound(Exception):
    pass


class EntryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    current_revision_id: UUID
    revision_number: int
    original_content: str
    entry_at: datetime
    created_at: datetime
    owner_date: date
    processing_state: Literal[
        "pending",
        "processing",
        "ready",
        "failed",
        "blocked_budget",
    ]


class TrashEntryRecord(EntryRecord):
    revision_count: int
    trashed_at: datetime


class CalendarDayCount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_date: date
    entry_count: int


class EntryRevisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    entry_id: UUID
    revision_number: int
    original_content: str
    created_at: datetime
    is_current: bool


@dataclass(frozen=True)
class HistorySlice:
    entries: list[EntryRecord]
    has_older: bool
    has_newer: bool
    older_cursor_entry_at: datetime | None
    older_cursor_entry_id: UUID | None
    newer_cursor_entry_at: datetime | None
    newer_cursor_entry_id: UUID | None
    snapshot: str


class HistoryMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    has_older: bool
    has_newer: bool
    older_cursor_entry_at: datetime | None
    older_cursor_entry_id: UUID | None
    newer_cursor_entry_at: datetime | None
    newer_cursor_entry_id: UUID | None
    snapshot: str


class SupabaseEntryStore:
    def __init__(self, settings: EntryStoreSettings) -> None:
        self._settings = settings

    async def create(
        self,
        *,
        access_token: str,
        original_content: str,
        entry_at: datetime | None,
        idempotency_key: str,
    ) -> tuple[EntryRecord, bool]:
        rows = await self._rpc(
            "create_diary_entry",
            {
                "p_original_content": original_content,
                "p_entry_at": (
                    entry_at.isoformat()
                    if entry_at is not None
                    else None
                ),
                "p_idempotency_key": idempotency_key,
            },
            access_token=access_token,
        )
        if len(rows) != 1:
            raise EntryStoreUnavailable

        row = dict(rows[0])
        was_created = row.pop("was_created", None)
        if not isinstance(was_created, bool):
            raise EntryStoreUnavailable

        try:
            return EntryRecord.model_validate(row), was_created
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def list_for_date(
        self,
        *,
        access_token: str,
        owner_date: date,
    ) -> list[EntryRecord]:
        rows = await self._rpc(
            "list_diary_entries_for_date",
            {
                "p_owner_date": owner_date.isoformat(),
            },
            access_token=access_token,
        )
        try:
            return [
                EntryRecord.model_validate(row)
                for row in rows
            ]
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def move_to_trash(
        self,
        *,
        access_token: str,
        entry_id: UUID,
    ) -> TrashEntryRecord:
        rows = await self._rpc(
            "move_diary_entry_to_trash",
            {"p_entry_id": str(entry_id)},
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        if len(rows) != 1:
            raise EntryStoreUnavailable
        try:
            return TrashEntryRecord.model_validate(rows[0])
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def list_trash(
        self,
        *,
        access_token: str,
    ) -> list[TrashEntryRecord]:
        rows = await self._rpc(
            "list_diary_trash",
            {},
            access_token=access_token,
        )
        try:
            return [
                TrashEntryRecord.model_validate(row)
                for row in rows
            ]
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def restore_from_trash(
        self,
        *,
        access_token: str,
        entry_id: UUID,
    ) -> EntryRecord:
        rows = await self._rpc(
            "restore_diary_entry_from_trash",
            {"p_entry_id": str(entry_id)},
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        if len(rows) != 1:
            raise EntryStoreUnavailable
        try:
            return EntryRecord.model_validate(rows[0])
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def permanently_delete(
        self,
        *,
        access_token: str,
        entry_id: UUID,
        confirmation: str,
    ) -> None:
        rows = await self._rpc(
            "permanently_delete_diary_entry",
            {
                "p_entry_id": str(entry_id),
                "p_confirmation": confirmation,
            },
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        if rows != [{"deleted": True}]:
            raise EntryStoreUnavailable

    async def get(
        self,
        *,
        access_token: str,
        entry_id: UUID,
    ) -> EntryRecord:
        rows = await self._rpc(
            "get_diary_entry",
            {"p_entry_id": str(entry_id)},
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        if len(rows) != 1:
            raise EntryStoreUnavailable
        try:
            return EntryRecord.model_validate(rows[0])
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def list_revisions(
        self,
        *,
        access_token: str,
        entry_id: UUID,
    ) -> list[EntryRevisionRecord]:
        rows = await self._rpc(
            "list_diary_entry_revisions",
            {"p_entry_id": str(entry_id)},
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        try:
            return [
                EntryRevisionRecord.model_validate(row)
                for row in rows
            ]
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def change_entry_time(
        self,
        *,
        access_token: str,
        entry_id: UUID,
        entry_at: datetime,
    ) -> EntryRecord:
        rows = await self._rpc(
            "change_diary_entry_time",
            {
                "p_entry_id": str(entry_id),
                "p_entry_at": entry_at.isoformat(),
            },
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        if len(rows) != 1:
            raise EntryStoreUnavailable
        try:
            return EntryRecord.model_validate(rows[0])
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def replace_original_content(
        self,
        *,
        access_token: str,
        entry_id: UUID,
        expected_current_revision_id: UUID,
        original_content: str,
    ) -> tuple[EntryRecord, bool]:
        rows = await self._rpc(
            "edit_diary_entry_original_content",
            {
                "p_entry_id": str(entry_id),
                "p_expected_current_revision_id": str(
                    expected_current_revision_id
                ),
                "p_original_content": original_content,
            },
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        if len(rows) != 1:
            raise EntryStoreUnavailable

        row = dict(rows[0])
        edit_applied = row.pop("edit_applied", None)
        if not isinstance(edit_applied, bool):
            raise EntryStoreUnavailable
        try:
            return EntryRecord.model_validate(row), edit_applied
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def restore_revision(
        self,
        *,
        access_token: str,
        entry_id: UUID,
        selected_revision_id: UUID,
        expected_current_revision_id: UUID,
    ) -> tuple[EntryRecord, bool]:
        rows = await self._rpc(
            "restore_diary_entry_revision",
            {
                "p_entry_id": str(entry_id),
                "p_selected_revision_id": str(selected_revision_id),
                "p_expected_current_revision_id": str(
                    expected_current_revision_id
                ),
            },
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound
        if len(rows) != 1:
            raise EntryStoreUnavailable

        row = dict(rows[0])
        restore_applied = row.pop("restore_applied", None)
        if not isinstance(restore_applied, bool):
            raise EntryStoreUnavailable
        try:
            return EntryRecord.model_validate(row), restore_applied
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def list_calendar_month(
        self,
        *,
        access_token: str,
        month: date,
    ) -> list[CalendarDayCount]:
        rows = await self._rpc(
            "list_diary_calendar_month",
            {
                "p_month": month.isoformat(),
            },
            access_token=access_token,
        )
        try:
            return [
                CalendarDayCount.model_validate(row)
                for row in rows
            ]
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def list_history(
        self,
        *,
        access_token: str,
        anchor_date: date,
        direction: Literal["initial", "older", "newer"],
        cursor_entry_at: datetime | None,
        cursor_entry_id: UUID | None,
        snapshot: str | None,
        limit: int,
    ) -> HistorySlice:
        rows = await self._rpc(
            "list_diary_history_v5",
            {
                "p_anchor_date": anchor_date.isoformat(),
                "p_direction": direction,
                "p_cursor_entry_at": (
                    cursor_entry_at.isoformat()
                    if cursor_entry_at is not None
                    else None
                ),
                "p_cursor_entry_id": (
                    str(cursor_entry_id)
                    if cursor_entry_id is not None
                    else None
                ),
                "p_snapshot": snapshot,
                "p_limit": limit,
            },
            access_token=access_token,
        )
        if not rows:
            raise EntryStoreUnavailable

        return self._parse_history_slice(rows)

    async def get_history_window(
        self,
        *,
        access_token: str,
        entry_id: UUID,
    ) -> HistorySlice:
        rows = await self._rpc(
            "get_diary_entry_history_window_v1",
            {"p_entry_id": str(entry_id)},
            access_token=access_token,
        )
        if not rows:
            raise EntryNotFound

        return self._parse_history_slice(rows)

    @staticmethod
    def _parse_history_slice(
        rows: list[dict[str, Any]],
    ) -> HistorySlice:
        first_metadata = {
            "has_older": rows[0].get("has_older"),
            "has_newer": rows[0].get("has_newer"),
            "older_cursor_entry_at": rows[0].get(
                "older_cursor_entry_at"
            ),
            "older_cursor_entry_id": rows[0].get(
                "older_cursor_entry_id"
            ),
            "newer_cursor_entry_at": rows[0].get(
                "newer_cursor_entry_at"
            ),
            "newer_cursor_entry_id": rows[0].get(
                "newer_cursor_entry_id"
            ),
            "snapshot": rows[0].get("snapshot"),
        }
        if not all(
            row.get(key) == value
            for row in rows
            for key, value in first_metadata.items()
        ):
            raise EntryStoreUnavailable

        entry_rows: list[dict[str, Any]] = []
        for row in rows:
            entry_row = dict(row)
            entry_row.pop("has_older", None)
            entry_row.pop("has_newer", None)
            entry_row.pop("older_cursor_entry_at", None)
            entry_row.pop("older_cursor_entry_id", None)
            entry_row.pop("newer_cursor_entry_at", None)
            entry_row.pop("newer_cursor_entry_id", None)
            entry_row.pop("snapshot", None)
            if entry_row.get("id") is None:
                if any(value is not None for value in entry_row.values()):
                    raise EntryStoreUnavailable
                continue
            entry_rows.append(entry_row)

        try:
            metadata = HistoryMetadata.model_validate(first_metadata)
            if not metadata.snapshot:
                raise ValueError
            if metadata.has_older != (
                metadata.older_cursor_entry_at is not None
                and metadata.older_cursor_entry_id is not None
            ) or metadata.has_newer != (
                metadata.newer_cursor_entry_at is not None
                and metadata.newer_cursor_entry_id is not None
            ):
                raise ValueError
            return HistorySlice(
                entries=[
                    EntryRecord.model_validate(row)
                    for row in entry_rows
                ],
                has_older=metadata.has_older,
                has_newer=metadata.has_newer,
                older_cursor_entry_at=metadata.older_cursor_entry_at,
                older_cursor_entry_id=metadata.older_cursor_entry_id,
                newer_cursor_entry_at=metadata.newer_cursor_entry_at,
                newer_cursor_entry_id=metadata.newer_cursor_entry_id,
                snapshot=metadata.snapshot,
            )
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def _rpc(
        self,
        name: str,
        payload: dict[str, object],
        *,
        access_token: str,
    ) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    (
                        f"{self._settings.supabase_url}"
                        f"/rest/v1/rpc/{name}"
                    ),
                    headers={
                        "Accept": "application/json",
                        "apikey": self._settings.publishable_key,
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.HTTPError as error:
            raise EntryStoreUnavailable from error

        if response.status_code != 200:
            raise EntryStoreUnavailable

        try:
            rows = response.json()
        except ValueError as error:
            raise EntryStoreUnavailable from error
        if not isinstance(rows, list) or not all(
            isinstance(row, dict) for row in rows
        ):
            raise EntryStoreUnavailable
        return rows


@lru_cache
def entry_store() -> SupabaseEntryStore:
    return SupabaseEntryStore(EntryStoreSettings.from_environment())
