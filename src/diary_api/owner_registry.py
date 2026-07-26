from __future__ import annotations

from functools import lru_cache
from uuid import UUID

import httpx

from diary_api.config import OwnerRegistrySettings


class OwnerRegistryUnavailable(Exception):
    pass


class SupabaseOwnerRegistry:
    def __init__(self, settings: OwnerRegistrySettings) -> None:
        self._settings = settings

    async def owner_id(self) -> UUID:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    (
                        f"{self._settings.supabase_url}"
                        "/rest/v1/diary_owners"
                    ),
                    headers={
                        "Accept": "application/json",
                        "apikey": self._settings.secret_key,
                        "Authorization": (
                            f"Bearer {self._settings.secret_key}"
                        ),
                    },
                    params={
                        "select": "user_id",
                        "limit": "2",
                    },
                )
        except httpx.HTTPError as error:
            raise OwnerRegistryUnavailable from error

        if response.status_code != 200:
            raise OwnerRegistryUnavailable

        try:
            rows = response.json()
            if not isinstance(rows, list) or len(rows) != 1:
                raise OwnerRegistryUnavailable
            row = rows[0]
            if not isinstance(row, dict):
                raise OwnerRegistryUnavailable
            return UUID(row["user_id"])
        except (KeyError, TypeError, ValueError) as error:
            raise OwnerRegistryUnavailable from error


@lru_cache
def owner_registry_settings() -> OwnerRegistrySettings:
    return OwnerRegistrySettings.from_environment()


@lru_cache
def owner_registry() -> SupabaseOwnerRegistry:
    return SupabaseOwnerRegistry(owner_registry_settings())
