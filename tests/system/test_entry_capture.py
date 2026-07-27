from datetime import UTC, datetime
from zoneinfo import ZoneInfo
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


def _postgrest_headers(
    settings: SupabaseSettings,
    access_token: str,
) -> dict[str, str]:
    return {
        "apikey": settings.publishable_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def test_owner_captures_original_content_and_sees_it_today(
    diary_api: str,
    owner_access_token: str,
) -> None:
    before_capture = datetime.now(UTC)
    response = httpx.post(
        f"{diary_api}/entries",
        headers={
            "Authorization": f"Bearer {owner_access_token}",
            "X-Idempotency-Key": "capture-today-tracer",
        },
        json={
            "original_content": (
                "完成 Ticket 03 的第一個垂直切片。\n"
                "Original Content 必須完整保留。"
            ),
        },
    )
    after_capture = datetime.now(UTC)

    assert response.status_code == 201
    captured = response.json()
    assert captured["original_content"] == (
        "完成 Ticket 03 的第一個垂直切片。\n"
        "Original Content 必須完整保留。"
    )
    assert captured["revision_number"] == 1
    assert captured["processing_state"] == "pending"
    assert before_capture <= datetime.fromisoformat(
        captured["entry_at"]
    ) <= after_capture
    assert before_capture <= datetime.fromisoformat(
        captured["created_at"]
    ) <= after_capture
    assert captured["owner_date"] == datetime.now(
        ZoneInfo("Asia/Taipei")
    ).date().isoformat()

    today_response = httpx.get(
        f"{diary_api}/entries/today",
        headers={
            "Authorization": f"Bearer {owner_access_token}",
        },
    )

    assert today_response.status_code == 200
    today_group = today_response.json()
    assert today_group["date"] == captured["owner_date"]
    captured_entries = [
        entry
        for entry in today_group["entries"]
        if entry["id"] == captured["id"]
    ]
    assert captured_entries == [captured]


def test_same_day_submissions_stay_separate_and_retries_are_idempotent(
    diary_api: str,
    owner_access_token: str,
) -> None:
    taipei_now = datetime.now(ZoneInfo("Asia/Taipei"))
    entry_time = taipei_now.replace(
        hour=9,
        minute=30,
        second=0,
        microsecond=0,
    ).isoformat()
    first_response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "same-day-first",
        },
        json={
            "original_content": "同一天的第一筆獨立 Entry。",
            "entry_at": entry_time,
        },
    )
    second_response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "same-day-second",
        },
        json={
            "original_content": "同一天的第二筆獨立 Entry。",
            "entry_at": entry_time,
        },
    )
    repeated_response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "same-day-first",
        },
        json={
            "original_content": "重送時不可覆寫原本內容。",
            "entry_at": entry_time,
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert repeated_response.status_code == 200
    first = first_response.json()
    second = second_response.json()
    repeated = repeated_response.json()
    assert first["id"] != second["id"]
    assert repeated == first

    today_response = httpx.get(
        f"{diary_api}/entries/today",
        headers=_owner_headers(owner_access_token),
    )
    entries = today_response.json()["entries"]
    entry_ids = [entry["id"] for entry in entries]
    assert entry_ids.count(first["id"]) == 1
    assert entry_ids.count(second["id"]) == 1


def test_backdated_entry_is_stored_as_utc_and_grouped_in_taipei(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "backdated-entry",
        },
        json={
            "original_content": "補記 7 月 24 日晚上的面試準備。",
            "entry_at": "2026-07-24T23:30:00+08:00",
        },
    )

    assert response.status_code == 201
    captured = response.json()
    assert datetime.fromisoformat(captured["entry_at"]) == datetime(
        2026,
        7,
        24,
        15,
        30,
        tzinfo=UTC,
    )
    assert captured["owner_date"] == "2026-07-24"

    stored_response = httpx.get(
        (
            f"{local_supabase.api_url}/rest/v1/entries"
            f"?id=eq.{captured['id']}&select=entry_at"
        ),
        headers=_postgrest_headers(
            local_supabase,
            owner_access_token,
        ),
    )
    assert stored_response.status_code == 200
    assert datetime.fromisoformat(
        stored_response.json()[0]["entry_at"]
    ) == datetime(2026, 7, 24, 15, 30, tzinfo=UTC)


def test_blank_capture_creates_no_partial_records(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "blank-rejection",
        },
        json={"original_content": " \n\t "},
    )

    assert response.status_code == 422
    stored_response = httpx.get(
        (
            f"{local_supabase.api_url}/rest/v1/entries"
            "?idempotency_key=eq.blank-rejection&select=id"
        ),
        headers=_postgrest_headers(
            local_supabase,
            owner_access_token,
        ),
    )
    assert stored_response.status_code == 200
    assert stored_response.json() == []


def test_rls_protects_entry_revision_and_processing_obligation(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "rls-entry",
        },
        json={"original_content": "只允許 owner 讀取的測試 Entry。"},
    )
    assert response.status_code == 201
    captured = response.json()

    resources = {
        "entries": captured["id"],
        "entry_revisions": captured["current_revision_id"],
        "ai_processing": captured["current_revision_id"],
    }
    for resource, identifier in resources.items():
        filter_name = (
            "entry_revision_id"
            if resource == "ai_processing"
            else "id"
        )
        resource_url = (
            f"{local_supabase.api_url}/rest/v1/{resource}"
            f"?{filter_name}=eq.{identifier}&select=*"
        )
        owner_response = httpx.get(
            resource_url,
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
        )
        non_owner_response = httpx.get(
            resource_url,
            headers=_postgrest_headers(
                local_supabase,
                non_owner_access_token,
            ),
        )
        assert owner_response.status_code == 200
        assert len(owner_response.json()) == 1
        assert non_owner_response.status_code == 200
        assert non_owner_response.json() == []

    mutation_response = httpx.post(
        f"{local_supabase.api_url}/rest/v1/entries",
        headers=_postgrest_headers(
            local_supabase,
            non_owner_access_token,
        ),
        json={
            "id": "7715126f-bc66-4218-b621-e12250215103",
            "owner_id": "0c97345c-50ac-4fcb-9664-bf796b854a92",
            "entry_at": "2026-07-27T00:00:00Z",
            "current_revision_id": (
                "47fceeb8-d4b7-450b-b51a-3c152b19dbd1"
            ),
            "idempotency_key": "forbidden",
            "created_at": "2026-07-27T00:00:00Z",
            "updated_at": "2026-07-27T00:00:00Z",
        },
    )
    assert mutation_response.status_code == 403

    non_owner_api_response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(non_owner_access_token),
            "X-Idempotency-Key": "non-owner-api",
        },
        json={"original_content": "不應建立。"},
    )
    assert non_owner_api_response.status_code == 401
    assert non_owner_api_response.json() == {
        "detail": "Authentication required"
    }


def test_entry_revisions_cannot_be_overwritten(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "immutable-revision",
        },
        json={"original_content": "這是必須保留的第一版原文。"},
    )
    assert response.status_code == 201
    captured = response.json()
    service_headers = {
        "apikey": local_supabase.service_role_key,
        "Authorization": f"Bearer {local_supabase.service_role_key}",
        "Content-Type": "application/json",
    }

    overwrite_response = httpx.patch(
        (
            f"{local_supabase.api_url}/rest/v1/entry_revisions"
            f"?id=eq.{captured['current_revision_id']}"
        ),
        headers=service_headers,
        json={"original_content": "不可以覆寫成這段內容。"},
    )

    assert overwrite_response.status_code == 400
    stored_response = httpx.get(
        (
            f"{local_supabase.api_url}/rest/v1/entry_revisions"
            f"?id=eq.{captured['current_revision_id']}"
            "&select=original_content"
        ),
        headers=_postgrest_headers(
            local_supabase,
            owner_access_token,
        ),
    )
    assert stored_response.json() == [
        {"original_content": "這是必須保留的第一版原文。"}
    ]
