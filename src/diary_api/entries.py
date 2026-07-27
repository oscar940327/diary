from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
from typing import Any, Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict

from diary_api.config import OwnerRegistrySettings
from diary_api.owner_registry import owner_registry_settings


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


class SupabaseEntryStore:
    def __init__(self, settings: OwnerRegistrySettings) -> None:
        self._settings = settings

    async def create(
        self,
        *,
        owner_id: UUID,
        original_content: str,
        entry_at: datetime | None,
        idempotency_key: str,
    ) -> tuple[EntryRecord, bool]:
        rows = await self._rpc(
            "create_diary_entry",
            {
                "p_owner_id": str(owner_id),
                "p_original_content": original_content,
                "p_entry_at": (
                    entry_at.isoformat()
                    if entry_at is not None
                    else None
                ),
                "p_idempotency_key": idempotency_key,
            },
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
        owner_id: UUID,
        owner_date: date,
    ) -> list[EntryRecord]:
        rows = await self._rpc(
            "list_diary_entries_for_date",
            {
                "p_owner_id": str(owner_id),
                "p_owner_date": owner_date.isoformat(),
            },
        )
        try:
            return [
                EntryRecord.model_validate(row)
                for row in rows
            ]
        except ValueError as error:
            raise EntryStoreUnavailable from error

    async def _rpc(
        self,
        name: str,
        payload: dict[str, object],
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
                        "apikey": self._settings.secret_key,
                        "Authorization": (
                            f"Bearer {self._settings.secret_key}"
                        ),
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
    return SupabaseEntryStore(owner_registry_settings())
