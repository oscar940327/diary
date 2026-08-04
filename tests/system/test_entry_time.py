from __future__ import annotations

from datetime import datetime, timezone
from contextlib import AbstractContextManager
from typing import Callable, Protocol, cast

import httpx


class SupabaseSettings(Protocol):
    api_url: str
    publishable_key: str


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


def _capture_entry(
    diary_api: str,
    access_token: str,
    *,
    content: str,
    entry_at: str,
    idempotency_key: str,
) -> dict[str, object]:
    response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(access_token),
            "X-Idempotency-Key": idempotency_key,
        },
        json={
            "entry_at": entry_at,
            "original_content": content,
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


def _revision_history(
    diary_api: str,
    access_token: str,
    entry_id: object,
) -> dict[str, object]:
    response = httpx.get(
        f"{diary_api}/entries/{entry_id}/revisions",
        headers=_owner_headers(access_token),
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, object], response.json())


def _processing_obligations(
    settings: SupabaseSettings,
    access_token: str,
    revision_id: object,
) -> list[dict[str, object]]:
    response = httpx.get(
        (
            f"{settings.api_url}/rest/v1/ai_processing"
            "?select=entry_revision_id,state,draft_required,"
            "embedding_required,attempt_count,created_at,updated_at,stale_at"
            f"&entry_revision_id=eq.{revision_id}"
        ),
        headers=_postgrest_headers(settings, access_token),
    )
    assert response.status_code == 200, response.text
    return cast(list[dict[str, object]], response.json())


def _history_positions(
    settings: SupabaseSettings,
    access_token: str,
    entry_id: object,
) -> list[dict[str, object]]:
    response = httpx.get(
        (
            f"{settings.api_url}/rest/v1/entry_history_positions"
            "?select=entry_id,entry_at,valid_from_xid,valid_until_xid"
            f"&entry_id=eq.{entry_id}"
            "&order=valid_from_xid.asc"
        ),
        headers=_postgrest_headers(settings, access_token),
    )
    assert response.status_code == 200, response.text
    return cast(list[dict[str, object]], response.json())


def _table_rows(
    settings: SupabaseSettings,
    access_token: str,
    table: str,
    select: str,
) -> list[dict[str, object]]:
    response = httpx.get(
        f"{settings.api_url}/rest/v1/{table}",
        headers=_postgrest_headers(settings, access_token),
        params={"select": select, "order": "created_at.asc"}
        if "created_at" in select
        else {"select": select},
    )
    assert response.status_code == 200, response.text
    return cast(list[dict[str, object]], response.json())


def _calendar_counts(
    diary_api: str,
    access_token: str,
    month: str,
) -> dict[str, int]:
    response = httpx.get(
        f"{diary_api}/entries/calendar",
        headers=_owner_headers(access_token),
        params={"month": month},
    )
    assert response.status_code == 200, response.text
    return {
        day["date"]: day["entry_count"]
        for day in response.json()["days"]
    }


def _history_entries(
    diary_api: str,
    access_token: str,
    anchor_date: str,
) -> list[dict[str, object]]:
    response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(access_token),
        params={"anchor_date": anchor_date, "limit": 50},
    )
    assert response.status_code == 200, response.text
    return cast(
        list[dict[str, object]],
        [
            entry
            for group in response.json()["groups"]
            for entry in group["entries"]
        ],
    )


def test_same_day_entry_time_change_updates_only_entry_metadata(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Entry Time changes must not change Original Content.",
        entry_at="2081-01-10T08:15:00.123456+08:00",
        idempotency_key="same-day-entry-time-change",
    )
    revisions_before = _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    )
    processing_before = _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    )

    response = httpx.put(
        f"{diary_api}/entries/{original['id']}/entry-time",
        headers=_owner_headers(owner_access_token),
        json={"entry_at": "2081-01-10T09:45:30.654321+08:00"},
    )

    assert response.status_code == 200, response.text
    changed = response.json()
    assert datetime.fromisoformat(changed["entry_at"]) == datetime.fromisoformat(
        "2081-01-10T09:45:30.654321+08:00"
    )
    assert changed["owner_date"] == "2081-01-10"
    assert {
        field: changed[field]
        for field in (
            "id",
            "created_at",
            "current_revision_id",
            "revision_number",
            "original_content",
            "processing_state",
        )
    } == {
        field: original[field]
        for field in (
            "id",
            "created_at",
            "current_revision_id",
            "revision_number",
            "original_content",
            "processing_state",
        )
    }
    assert _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    ) == revisions_before
    assert _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    ) == processing_before


def test_cross_day_change_regroups_history_and_updates_calendar_counts(
    diary_api: str,
    owner_access_token: str,
) -> None:
    old_day_sentinel = _capture_entry(
        diary_api,
        owner_access_token,
        content="This Entry stays on the old Taipei date.",
        entry_at="2081-02-01T10:00:00+08:00",
        idempotency_key="entry-time-old-day-sentinel",
    )
    new_day_sentinel = _capture_entry(
        diary_api,
        owner_access_token,
        content="This Entry stays on the new Taipei date.",
        entry_at="2081-02-02T10:00:00+08:00",
        idempotency_key="entry-time-new-day-sentinel",
    )
    moving = _capture_entry(
        diary_api,
        owner_access_token,
        content="This Entry moves across a Taipei date boundary.",
        entry_at="2081-02-01T23:59:59.999999+08:00",
        idempotency_key="entry-time-cross-day-move",
    )
    assert _calendar_counts(
        diary_api,
        owner_access_token,
        "2081-02",
    ) == {
        "2081-02-01": 2,
        "2081-02-02": 1,
    }

    response = httpx.put(
        f"{diary_api}/entries/{moving['id']}/entry-time",
        headers=_owner_headers(owner_access_token),
        json={"entry_at": "2081-02-02T00:00:00+08:00"},
    )

    assert response.status_code == 200, response.text
    changed = response.json()
    assert changed["owner_date"] == "2081-02-02"
    assert _calendar_counts(
        diary_api,
        owner_access_token,
        "2081-02",
    ) == {
        "2081-02-01": 1,
        "2081-02-02": 2,
    }
    entries = _history_entries(
        diary_api,
        owner_access_token,
        "2081-02-02",
    )
    entries_by_id = {entry["id"]: entry for entry in entries}
    assert entries_by_id[old_day_sentinel["id"]]["owner_date"] == (
        "2081-02-01"
    )
    assert entries_by_id[new_day_sentinel["id"]]["owner_date"] == (
        "2081-02-02"
    )
    assert entries_by_id[moving["id"]] == changed


def test_existing_history_snapshot_does_not_duplicate_a_moved_entry(
    diary_api: str,
    owner_access_token: str,
) -> None:
    oldest = _capture_entry(
        diary_api,
        owner_access_token,
        content="Snapshot position one.",
        entry_at="2082-04-01T12:00:00+08:00",
        idempotency_key="entry-time-snapshot-position-one",
    )
    older = _capture_entry(
        diary_api,
        owner_access_token,
        content="Snapshot position two.",
        entry_at="2082-04-02T12:00:00+08:00",
        idempotency_key="entry-time-snapshot-position-two",
    )
    moving = _capture_entry(
        diary_api,
        owner_access_token,
        content="Snapshot position three moves after page one.",
        entry_at="2082-04-03T12:00:00+08:00",
        idempotency_key="entry-time-snapshot-position-three",
    )
    newest = _capture_entry(
        diary_api,
        owner_access_token,
        content="Snapshot position four.",
        entry_at="2082-04-04T12:00:00+08:00",
        idempotency_key="entry-time-snapshot-position-four",
    )

    initial_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={"anchor_date": "2082-04-04", "limit": 2},
    )
    assert initial_response.status_code == 200, initial_response.text
    initial = initial_response.json()
    assert [
        entry["id"]
        for group in initial["groups"]
        for entry in group["entries"]
    ] == [newest["id"], moving["id"]]
    assert initial["older_cursor"] is not None

    change_response = httpx.put(
        f"{diary_api}/entries/{moving['id']}/entry-time",
        headers=_owner_headers(owner_access_token),
        json={"entry_at": "2082-04-02T18:00:00+08:00"},
    )
    assert change_response.status_code == 200, change_response.text

    older_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "cursor": initial["older_cursor"],
            "direction": "older",
            "limit": 2,
        },
    )

    assert older_response.status_code == 200, older_response.text
    assert [
        entry["id"]
        for group in older_response.json()["groups"]
        for entry in group["entries"]
    ] == [older["id"], oldest["id"]]


def test_existing_history_snapshot_does_not_omit_an_unvisited_moved_entry(
    diary_api: str,
    owner_access_token: str,
) -> None:
    oldest = _capture_entry(
        diary_api,
        owner_access_token,
        content="Unvisited snapshot position one.",
        entry_at="2082-05-01T12:00:00+08:00",
        idempotency_key="entry-time-unvisited-position-one",
    )
    moving = _capture_entry(
        diary_api,
        owner_access_token,
        content="Unvisited snapshot position two moves before page two.",
        entry_at="2082-05-02T12:00:00+08:00",
        idempotency_key="entry-time-unvisited-position-two",
    )
    boundary = _capture_entry(
        diary_api,
        owner_access_token,
        content="Unvisited snapshot position three.",
        entry_at="2082-05-03T12:00:00+08:00",
        idempotency_key="entry-time-unvisited-position-three",
    )
    newest = _capture_entry(
        diary_api,
        owner_access_token,
        content="Unvisited snapshot position four.",
        entry_at="2082-05-04T12:00:00+08:00",
        idempotency_key="entry-time-unvisited-position-four",
    )
    initial_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={"anchor_date": "2082-05-04", "limit": 2},
    )
    assert initial_response.status_code == 200, initial_response.text
    initial = initial_response.json()
    assert [
        entry["id"]
        for group in initial["groups"]
        for entry in group["entries"]
    ] == [newest["id"], boundary["id"]]

    change_response = httpx.put(
        f"{diary_api}/entries/{moving['id']}/entry-time",
        headers=_owner_headers(owner_access_token),
        json={"entry_at": "2082-05-05T12:00:00+08:00"},
    )
    assert change_response.status_code == 200, change_response.text

    older_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "cursor": initial["older_cursor"],
            "direction": "older",
            "limit": 2,
        },
    )
    assert older_response.status_code == 200, older_response.text
    assert [
        entry["id"]
        for group in older_response.json()["groups"]
        for entry in group["entries"]
    ] == [moving["id"], oldest["id"]]


def test_timezone_boundary_and_equal_timestamp_use_taipei_date_and_uuid_order(
    diary_api: str,
    owner_access_token: str,
) -> None:
    peer = _capture_entry(
        diary_api,
        owner_access_token,
        content="Equal-time peer already on July first.",
        entry_at="2082-07-01T00:00:00+08:00",
        idempotency_key="entry-time-equal-peer",
    )
    moving = _capture_entry(
        diary_api,
        owner_access_token,
        content="Moves across the UTC to Taipei date boundary.",
        entry_at="2082-06-30T23:00:00+08:00",
        idempotency_key="entry-time-timezone-boundary",
    )

    response = httpx.put(
        f"{diary_api}/entries/{moving['id']}/entry-time",
        headers=_owner_headers(owner_access_token),
        json={"entry_at": "2082-06-30T16:00:00+00:00"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["owner_date"] == "2082-07-01"
    assert _calendar_counts(diary_api, owner_access_token, "2082-06") == {}
    assert _calendar_counts(diary_api, owner_access_token, "2082-07") == {
        "2082-07-01": 2,
    }
    equal_time_entries = [
        entry
        for entry in _history_entries(
            diary_api,
            owner_access_token,
            "2082-07-01",
        )
        if entry["id"] in {peer["id"], moving["id"]}
    ]
    assert [entry["id"] for entry in equal_time_entries] == sorted(
        [str(peer["id"]), str(moving["id"])],
        reverse=True,
    )
    assert len({entry["entry_at"] for entry in equal_time_entries}) == 1


def test_invalid_or_offsetless_entry_time_is_rejected_without_partial_change(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Invalid Entry Time must leave this Entry unchanged.",
        entry_at="2082-08-01T12:00:00+08:00",
        idempotency_key="entry-time-invalid-input",
    )
    revisions_before = _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    )
    processing_before = _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    )

    for entry_at in (
        "2082-08-02T12:00:00",
        "not-a-timestamp",
        "2082-08-02T12:00:00+25:00",
    ):
        response = httpx.put(
            f"{diary_api}/entries/{original['id']}/entry-time",
            headers=_owner_headers(owner_access_token),
            json={"entry_at": entry_at},
        )
        assert response.status_code == 422, response.text

    missing_response = httpx.put(
        f"{diary_api}/entries/{original['id']}/entry-time",
        headers=_owner_headers(owner_access_token),
        json={},
    )
    assert missing_response.status_code == 422, missing_response.text

    for entry_at in ("2082-08-02T12:00:00", "not-a-timestamp"):
        direct_rpc_response = httpx.post(
            (
                f"{local_supabase.api_url}/rest/v1/rpc/"
                "change_diary_entry_time"
            ),
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
            json={
                "p_entry_id": original["id"],
                "p_entry_at": entry_at,
            },
        )
        assert direct_rpc_response.status_code == 400

    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == original
    assert _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    ) == revisions_before
    assert _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    ) == processing_before


def test_fastapi_rejects_utc_normalization_overflow_without_partial_change(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="FastAPI boundary validation must be atomic.",
        entry_at="2082-08-10T12:00:00+08:00",
        idempotency_key="entry-time-fastapi-range-validation",
    )
    revisions_before = _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    )
    processing_before = _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    )
    positions_before = _history_positions(
        local_supabase,
        owner_access_token,
        original["id"],
    )

    for body in (
        {"entry_at": "9999-12-31T23:59:59.999999-14:00"},
        {"entry_at": "0001-01-01T00:00:00+14:00"},
        {"entry_at": "10000-01-01T00:00:00+00:00"},
        {"entry_at": "2082-08-11T12:00:00"},
        {"entry_at": "2082-08-11T12:00:00+25:00"},
        {},
    ):
        response = httpx.put(
            f"{diary_api}/entries/{original['id']}/entry-time",
            headers=_owner_headers(owner_access_token),
            json=body,
        )
        assert response.status_code == 422, response.text

    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == original
    assert _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    ) == revisions_before
    assert _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    ) == processing_before
    assert _history_positions(
        local_supabase,
        owner_access_token,
        original["id"],
    ) == positions_before


def test_direct_rpc_rejects_python_unsafe_timestamps_without_partial_change(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="The direct RPC cannot create unreadable metadata.",
        entry_at="2082-08-20T12:00:00+08:00",
        idempotency_key="entry-time-rpc-range-validation",
    )
    revisions_before = _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    )
    processing_before = _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    )
    positions_before = _history_positions(
        local_supabase,
        owner_access_token,
        original["id"],
    )
    endpoint = (
        f"{local_supabase.api_url}/rest/v1/rpc/change_diary_entry_time"
    )

    for body in (
        {
            "p_entry_id": original["id"],
            "p_entry_at": "9999-12-31T23:59:59.999999-14:00",
        },
        {
            "p_entry_id": original["id"],
            "p_entry_at": "0001-01-01T00:00:00+14:00",
        },
        {
            "p_entry_id": original["id"],
            "p_entry_at": "10000-01-01T00:00:00+00:00",
        },
        {
            "p_entry_id": original["id"],
            "p_entry_at": "2082-08-21T12:00:00",
        },
        {
            "p_entry_id": original["id"],
            "p_entry_at": "2082-08-21T12:00:00+25:00",
        },
        {"p_entry_id": original["id"]},
    ):
        response = httpx.post(
            endpoint,
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
            json=body,
        )
        assert response.status_code == 400, response.text

    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == original
    assert _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    ) == revisions_before
    assert _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    ) == processing_before
    assert _history_positions(
        local_supabase,
        owner_access_token,
        original["id"],
    ) == positions_before


def test_direct_create_rpc_rejects_python_unsafe_timestamps_before_writes(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    endpoint = f"{local_supabase.api_url}/rest/v1/rpc/create_diary_entry"
    table_selections = {
        "entries": (
            "id,entry_at,idempotency_key,current_revision_id,created_at"
        ),
        "entry_revisions": "id,entry_id,original_content,created_at",
        "ai_processing": "id,entry_revision_id,state,created_at",
        "entry_history_positions": (
            "entry_id,entry_at,valid_from_xid,valid_until_xid"
        ),
    }
    rows_before = {
        table: _table_rows(
            local_supabase,
            owner_access_token,
            table,
            select,
        )
        for table, select in table_selections.items()
    }
    unsafe_timestamps = (
        "10000-01-01T00:00:00+00:00",
        "9999-12-31T23:59:59.999999-14:00",
        "0001-01-01T00:00:00+14:00",
        "2082-08-21T12:00:00",
        "2082-08-21T12:00:00+25:00",
    )

    for index, entry_at in enumerate(unsafe_timestamps):
        response = httpx.post(
            endpoint,
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
            json={
                "p_original_content": (
                    f"Unsafe direct Create RPC boundary {index}."
                ),
                "p_entry_at": entry_at,
                "p_idempotency_key": f"unsafe-direct-create-{index}",
            },
        )
        assert response.status_code == 400, response.text

    assert {
        table: _table_rows(
            local_supabase,
            owner_access_token,
            table,
            select,
        )
        for table, select in table_selections.items()
    } == rows_before

    for suffix, optional_entry_at in (
        ("omitted", ...),
        ("null", None),
    ):
        body: dict[str, object] = {
            "p_original_content": (
                f"Direct Create defaults Entry Time when {suffix}."
            ),
            "p_idempotency_key": f"direct-create-default-{suffix}",
        }
        if optional_entry_at is not ...:
            body["p_entry_at"] = optional_entry_at
        response = httpx.post(
            endpoint,
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
            json=body,
        )
        assert response.status_code == 200, response.text
        created = response.json()
        assert len(created) == 1
        assert created[0]["was_created"] is True
        parsed_entry_at = datetime.fromisoformat(created[0]["entry_at"])
        assert parsed_entry_at.tzinfo is not None
        assert abs(
            (datetime.now(timezone.utc) - parsed_entry_at).total_seconds()
        ) < 30
        detail_response = httpx.get(
            f"{diary_api}/entries/{created[0]['id']}",
            headers=_owner_headers(owner_access_token),
        )
        assert detail_response.status_code == 200, detail_response.text

    application_response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(owner_access_token),
            "X-Idempotency-Key": "application-create-after-expand",
        },
        json={
            "entry_at": "2082-08-22T12:00:00+08:00",
            "original_content": (
                "The existing application revision can still Create Entry."
            ),
        },
    )
    assert application_response.status_code == 201, application_response.text


def test_owner_cannot_patch_entry_metadata_outside_controlled_action(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Direct metadata patches must be denied.",
        entry_at="2082-09-01T12:00:00+08:00",
        idempotency_key="deny-direct-entry-metadata-patch",
    )

    direct_patch_response = httpx.patch(
        (
            f"{local_supabase.api_url}/rest/v1/entries"
            f"?id=eq.{original['id']}"
        ),
        headers=_postgrest_headers(local_supabase, owner_access_token),
        json={
            "created_at": "2000-01-01T00:00:00+00:00",
            "entry_at": "2000-01-01T00:00:00+00:00",
        },
    )

    assert direct_patch_response.status_code == 403
    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == original


def test_entry_time_change_rolls_back_when_rls_denies_entry_update(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    deny_entry_updates: Callable[[], AbstractContextManager[None]],
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="RLS denial must preserve every Entry Time invariant.",
        entry_at="2082-10-01T12:00:00+08:00",
        idempotency_key="entry-time-rls-rollback",
    )
    revisions_before = _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    )
    processing_before = _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    )

    with deny_entry_updates():
        response = httpx.put(
            f"{diary_api}/entries/{original['id']}/entry-time",
            headers=_owner_headers(owner_access_token),
            json={"entry_at": "2082-10-02T12:00:00+08:00"},
        )

    assert response.status_code == 503, response.text
    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == original
    assert _revision_history(
        diary_api,
        owner_access_token,
        original["id"],
    ) == revisions_before
    assert _processing_obligations(
        local_supabase,
        owner_access_token,
        original["current_revision_id"],
    ) == processing_before


def test_entry_time_change_requires_owner_at_fastapi_and_postgres_rls(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Both authorization layers must protect Entry Time.",
        entry_at="2082-11-01T12:00:00+08:00",
        idempotency_key="entry-time-defense-in-depth",
    )
    endpoint = f"{diary_api}/entries/{original['id']}/entry-time"

    missing_response = httpx.put(
        endpoint,
        json={"entry_at": "2082-11-02T12:00:00+08:00"},
    )
    non_owner_response = httpx.put(
        endpoint,
        headers=_owner_headers(non_owner_access_token),
        json={"entry_at": "2082-11-02T12:00:00+08:00"},
    )
    direct_non_owner_response = httpx.post(
        (
            f"{local_supabase.api_url}/rest/v1/rpc/"
            "change_diary_entry_time"
        ),
        headers=_postgrest_headers(
            local_supabase,
            non_owner_access_token,
        ),
        json={
            "p_entry_id": original["id"],
            "p_entry_at": "2082-11-02T12:00:00+08:00",
        },
    )

    assert missing_response.status_code == 401
    assert non_owner_response.status_code == 401
    assert direct_non_owner_response.status_code == 200
    assert direct_non_owner_response.json() == []
    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == original
