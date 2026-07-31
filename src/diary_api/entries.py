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


class CalendarDayCount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_date: date
    entry_count: int


@dataclass(frozen=True)
class HistorySlice:
    entries: list[EntryRecord]
    has_older: bool
    has_newer: bool
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
            "list_diary_history_v2",
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
            return HistorySlice(
                entries=[],
                has_older=False,
                has_newer=False,
                snapshot=snapshot or "",
            )

        first_metadata = {
            "has_older": rows[0].get("has_older"),
            "has_newer": rows[0].get("has_newer"),
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
            entry_row.pop("snapshot", None)
            entry_rows.append(entry_row)

        try:
            has_older = first_metadata["has_older"]
            has_newer = first_metadata["has_newer"]
            parsed_snapshot = first_metadata["snapshot"]
            if not isinstance(has_older, bool) or not isinstance(
                has_newer,
                bool,
            ) or not isinstance(parsed_snapshot, str) or not parsed_snapshot:
                raise ValueError
            return HistorySlice(
                entries=[
                    EntryRecord.model_validate(row)
                    for row in entry_rows
                ],
                has_older=has_older,
                has_newer=has_newer,
                snapshot=parsed_snapshot,
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
