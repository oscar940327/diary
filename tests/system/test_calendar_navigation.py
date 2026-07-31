from collections.abc import Iterable
from typing import Protocol

import httpx


class SupabaseSettings(Protocol):
    api_url: str
    publishable_key: str
    service_role_key: str


def _owner_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
    }


def _capture_entries(
    diary_api: str,
    access_token: str,
    entries: Iterable[tuple[str, str, str]],
) -> list[dict[str, object]]:
    captured_entries: list[dict[str, object]] = []
    for idempotency_key, original_content, entry_at in entries:
        response = httpx.post(
            f"{diary_api}/entries",
            headers={
                **_owner_headers(access_token),
                "X-Idempotency-Key": idempotency_key,
            },
            json={
                "original_content": original_content,
                "entry_at": entry_at,
            },
        )
        assert response.status_code == 201
        captured_entries.append(response.json())
    return captured_entries


def test_calendar_counts_entries_inside_taipei_month_boundaries(
    diary_api: str,
    owner_access_token: str,
) -> None:
    _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                "calendar-before-march",
                "Must not cross into the requested month.",
                "2040-02-29T15:59:59+00:00",
            ),
            (
                "calendar-march-first-a",
                "First Entry at Taipei month start.",
                "2040-02-29T16:00:00+00:00",
            ),
            (
                "calendar-march-first-b",
                "Second Entry on the same Taipei date.",
                "2040-03-01T04:00:00+00:00",
            ),
            (
                "calendar-march-last",
                "Last Entry inside the Taipei month.",
                "2040-03-31T15:59:59+00:00",
            ),
            (
                "calendar-after-march",
                "Must not remain in the requested month.",
                "2040-03-31T16:00:00+00:00",
            ),
        ),
    )

    response = httpx.get(
        f"{diary_api}/entries/calendar",
        headers=_owner_headers(owner_access_token),
        params={"month": "2040-03"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "month": "2040-03",
        "time_zone": "Asia/Taipei",
        "days": [
            {"date": "2040-03-01", "entry_count": 2},
            {"date": "2040-03-31", "entry_count": 1},
        ],
    }


def test_calendar_excludes_trashed_entries_and_preserves_owner_defenses(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    captured = _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                "calendar-active-entry",
                "Active Calendar content must not be returned.",
                "2041-06-15T04:00:00+00:00",
            ),
            (
                "calendar-trashed-entry",
                "Trashed Calendar content must not affect counts.",
                "2041-06-15T05:00:00+00:00",
            ),
        ),
    )
    trashed_entry_id = captured[1]["id"]
    trash_response = httpx.patch(
        (
            f"{local_supabase.api_url}/rest/v1/entries"
            f"?id=eq.{trashed_entry_id}"
        ),
        headers={
            "apikey": local_supabase.service_role_key,
            "Authorization": (
                f"Bearer {local_supabase.service_role_key}"
            ),
            "Content-Type": "application/json",
        },
        json={"trashed_at": "2041-06-16T00:00:00+00:00"},
    )
    assert trash_response.status_code == 204

    response = httpx.get(
        f"{diary_api}/entries/calendar",
        headers=_owner_headers(owner_access_token),
        params={"month": "2041-06"},
    )

    assert response.status_code == 200
    assert response.json()["days"] == [
        {"date": "2041-06-15", "entry_count": 1}
    ]
    assert "Active Calendar content" not in response.text
    assert "Trashed Calendar content" not in response.text

    non_owner_response = httpx.get(
        f"{diary_api}/entries/calendar",
        headers=_owner_headers(non_owner_access_token),
        params={"month": "2041-06"},
    )
    assert non_owner_response.status_code == 401
    assert non_owner_response.json() == {
        "detail": "Authentication required"
    }

    non_owner_rls_response = httpx.post(
        (
            f"{local_supabase.api_url}"
            "/rest/v1/rpc/list_diary_calendar_month"
        ),
        headers={
            "apikey": local_supabase.publishable_key,
            "Authorization": f"Bearer {non_owner_access_token}",
            "Content-Type": "application/json",
        },
        json={"p_month": "2041-06-01"},
    )
    assert non_owner_rls_response.status_code == 200
    assert non_owner_rls_response.json() == []


def test_empty_calendar_date_anchors_bidirectional_continuous_history(
    diary_api: str,
    owner_access_token: str,
) -> None:
    _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                "calendar-history-newer",
                "Newer Calendar-adjacent Entry.",
                "2042-09-20T04:00:00+00:00",
            ),
            (
                "calendar-history-nearby",
                "Nearby Entry before the empty anchor.",
                "2042-09-10T04:00:00+00:00",
            ),
            (
                "calendar-history-older",
                "Older Calendar-adjacent Entry.",
                "2042-09-01T04:00:00+00:00",
            ),
        ),
    )

    calendar_response = httpx.get(
        f"{diary_api}/entries/calendar",
        headers=_owner_headers(owner_access_token),
        params={"month": "2042-09"},
    )
    assert calendar_response.status_code == 200
    assert calendar_response.json()["days"] == [
        {"date": "2042-09-01", "entry_count": 1},
        {"date": "2042-09-10", "entry_count": 1},
        {"date": "2042-09-20", "entry_count": 1},
    ]

    anchor_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={"anchor_date": "2042-09-15", "limit": 1},
    )
    assert anchor_response.status_code == 200
    anchor_page = anchor_response.json()
    assert anchor_page["anchor_date"] == "2042-09-15"
    assert anchor_page["groups"][0]["date"] == "2042-09-10"
    assert anchor_page["older_cursor"] is not None
    assert anchor_page["newer_cursor"] is not None

    newer_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "cursor": anchor_page["newer_cursor"],
            "direction": "newer",
            "limit": 1,
        },
    )
    older_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "cursor": anchor_page["older_cursor"],
            "direction": "older",
            "limit": 1,
        },
    )

    assert newer_response.status_code == 200
    assert newer_response.json()["groups"][0]["date"] == "2042-09-20"
    assert older_response.status_code == 200
    assert older_response.json()["groups"][0]["date"] == "2042-09-01"
