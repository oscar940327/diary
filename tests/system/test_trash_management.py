from __future__ import annotations

import subprocess
from typing import Protocol, cast
from uuid import uuid4

import httpx


class SupabaseSettings(Protocol):
    api_url: str
    publishable_key: str
    service_role_key: str


def _owner_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


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


def _postgrest_headers(
    settings: SupabaseSettings,
    access_token: str,
) -> dict[str, str]:
    return {
        "apikey": settings.publishable_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _service_headers(settings: SupabaseSettings) -> dict[str, str]:
    return {
        "apikey": settings.service_role_key,
        "Authorization": f"Bearer {settings.service_role_key}",
        "Content-Type": "application/json",
    }


def _history_entries(page: dict[str, object]) -> list[dict[str, object]]:
    groups = cast(list[dict[str, object]], page["groups"])
    return [
        cast(dict[str, object], entry)
        for group in groups
        for entry in cast(list[object], group["entries"])
    ]


def test_owner_moves_entry_to_trash_and_normal_views_exclude_it(
    diary_api: str,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Ticket 09 Revision 1 to keep in recoverable Trash.",
        entry_at="2050-04-05T15:59:59.123456+00:00",
        idempotency_key="ticket-09-trash-listing",
    )
    edit_response = httpx.put(
        f"{diary_api}/entries/{original['id']}/original-content",
        headers=_owner_headers(owner_access_token),
        json={
            "expected_current_revision_id": original["current_revision_id"],
            "original_content": (
                "Ticket 09 Revision 2 current content for Trash review."
            ),
        },
    )
    assert edit_response.status_code == 200, edit_response.text
    current = cast(dict[str, object], edit_response.json())

    trash_response = httpx.post(
        f"{diary_api}/entries/{original['id']}/trash",
        headers=_owner_headers(owner_access_token),
    )

    assert trash_response.status_code == 200, trash_response.text
    trashed = trash_response.json()
    assert trashed == {
        "id": original["id"],
        "current_revision_id": current["current_revision_id"],
        "revision_number": 2,
        "revision_count": 2,
        "original_content": current["original_content"],
        "entry_at": current["entry_at"],
        "created_at": current["created_at"],
        "owner_date": "2050-04-05",
        "processing_state": "pending",
        "trashed_at": trashed["trashed_at"],
    }
    assert isinstance(trashed["trashed_at"], str)

    listing_response = httpx.get(
        f"{diary_api}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert listing_response.status_code == 200, listing_response.text
    listed = [
        entry
        for entry in listing_response.json()["entries"]
        if entry["id"] == original["id"]
    ]
    assert listed == [trashed]

    history_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={"anchor_date": "2050-04-05"},
    )
    assert history_response.status_code == 200, history_response.text
    assert original["id"] not in {
        entry["id"] for entry in _history_entries(history_response.json())
    }

    calendar_response = httpx.get(
        f"{diary_api}/entries/calendar",
        headers=_owner_headers(owner_access_token),
        params={"month": "2050-04"},
    )
    assert calendar_response.status_code == 200, calendar_response.text
    assert calendar_response.json()["days"] == []

    for path in (
        f"/entries/{original['id']}",
        f"/entries/{original['id']}/revisions",
        f"/entries/{original['id']}/history-window",
    ):
        response = httpx.get(
            f"{diary_api}{path}",
            headers=_owner_headers(owner_access_token),
        )
        assert response.status_code == 404, response.text
        assert response.json() == {"detail": "Entry not found"}


def test_owner_restores_trashed_entry_with_revisions_and_processing_intact(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Ticket 09 restore keeps Revision 1.",
        entry_at="2051-01-01T16:00:00.654321+00:00",
        idempotency_key="ticket-09-restore-entry",
    )
    edit_response = httpx.put(
        f"{diary_api}/entries/{original['id']}/original-content",
        headers=_owner_headers(owner_access_token),
        json={
            "expected_current_revision_id": original["current_revision_id"],
            "original_content": "Ticket 09 restore keeps Revision 2 current.",
        },
    )
    assert edit_response.status_code == 200, edit_response.text
    current = cast(dict[str, object], edit_response.json())

    before_revisions_response = httpx.get(
        f"{diary_api}/entries/{original['id']}/revisions",
        headers=_owner_headers(owner_access_token),
    )
    assert before_revisions_response.status_code == 200
    revisions_before = before_revisions_response.json()
    revision_ids = [
        revision["id"] for revision in revisions_before["revisions"]
    ]
    before_processing_response = httpx.get(
        f"{local_supabase.api_url}/rest/v1/ai_processing",
        headers=_postgrest_headers(local_supabase, owner_access_token),
        params={
            "select": "id,entry_revision_id,state,stale_at",
            "entry_revision_id": f"in.({','.join(revision_ids)})",
            "order": "created_at.desc",
        },
    )
    assert before_processing_response.status_code == 200
    processing_before = before_processing_response.json()

    trash_response = httpx.post(
        f"{diary_api}/entries/{original['id']}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert trash_response.status_code == 200, trash_response.text

    restore_response = httpx.post(
        f"{diary_api}/trash/{original['id']}/restore",
        headers=_owner_headers(owner_access_token),
    )

    assert restore_response.status_code == 200, restore_response.text
    restored = restore_response.json()
    assert restored == current
    assert restored["owner_date"] == "2051-01-02"

    trash_listing_response = httpx.get(
        f"{diary_api}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert trash_listing_response.status_code == 200
    assert original["id"] not in {
        entry["id"] for entry in trash_listing_response.json()["entries"]
    }

    revisions_response = httpx.get(
        f"{diary_api}/entries/{original['id']}/revisions",
        headers=_owner_headers(owner_access_token),
    )
    assert revisions_response.status_code == 200, revisions_response.text
    assert revisions_response.json() == revisions_before

    processing_response = httpx.get(
        f"{local_supabase.api_url}/rest/v1/ai_processing",
        headers=_postgrest_headers(local_supabase, owner_access_token),
        params={
            "select": "id,entry_revision_id,state,stale_at",
            "entry_revision_id": f"in.({','.join(revision_ids)})",
            "order": "created_at.desc",
        },
    )
    assert processing_response.status_code == 200
    assert processing_response.json() == processing_before

    history_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={"anchor_date": "2051-01-02"},
    )
    assert history_response.status_code == 200
    assert [
        entry
        for entry in _history_entries(history_response.json())
        if entry["id"] == original["id"]
    ] == [restored]

    calendar_response = httpx.get(
        f"{diary_api}/entries/calendar",
        headers=_owner_headers(owner_access_token),
        params={"month": "2051-01"},
    )
    assert calendar_response.status_code == 200
    assert calendar_response.json()["days"] == [
        {"date": "2051-01-02", "entry_count": 1}
    ]


def test_trash_operations_are_non_disclosing_and_rls_enforced(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    active = _capture_entry(
        diary_api,
        owner_access_token,
        content="Ticket 09 active non-disclosure control.",
        entry_at="2054-06-01T01:00:00+00:00",
        idempotency_key="ticket-09-security-active",
    )
    trashed = _capture_entry(
        diary_api,
        owner_access_token,
        content="Ticket 09 trashed non-disclosure control.",
        entry_at="2054-06-02T01:00:00+00:00",
        idempotency_key="ticket-09-security-trashed",
    )
    foreign = _capture_entry(
        diary_api,
        owner_access_token,
        content="Ticket 09 foreign-owner non-disclosure control.",
        entry_at="2054-06-03T01:00:00+00:00",
        idempotency_key="ticket-09-security-foreign",
    )
    move_response = httpx.post(
        f"{diary_api}/entries/{trashed['id']}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert move_response.status_code == 200
    foreign_response = httpx.patch(
        f"{local_supabase.api_url}/rest/v1/entries",
        headers=_service_headers(local_supabase),
        params={"id": f"eq.{foreign['id']}"},
        json={"owner_id": "0c97345c-50ac-4fcb-9664-bf796b854a92"},
    )
    assert foreign_response.status_code == 204, foreign_response.text
    missing_id = str(uuid4())

    owner_denials = [
        httpx.post(
            f"{diary_api}/entries/{entry_id}/trash",
            headers=_owner_headers(owner_access_token),
        )
        for entry_id in (foreign["id"], trashed["id"], missing_id)
    ] + [
        httpx.post(
            f"{diary_api}/trash/{entry_id}/restore",
            headers=_owner_headers(owner_access_token),
        )
        for entry_id in (foreign["id"], active["id"], missing_id)
    ] + [
        httpx.request(
            "DELETE",
            f"{diary_api}/trash/{entry_id}",
            headers=_owner_headers(owner_access_token),
            json={"confirmation": "PERMANENTLY DELETE"},
        )
        for entry_id in (foreign["id"], active["id"], missing_id)
    ]
    assert {
        (response.status_code, response.text) for response in owner_denials
    } == {(404, '{"detail":"Entry not found"}')}

    non_owner_api_responses = [
        httpx.get(
            f"{diary_api}/trash",
            headers=_owner_headers(non_owner_access_token),
        ),
        httpx.post(
            f"{diary_api}/entries/{active['id']}/trash",
            headers=_owner_headers(non_owner_access_token),
        ),
        httpx.post(
            f"{diary_api}/trash/{trashed['id']}/restore",
            headers=_owner_headers(non_owner_access_token),
        ),
        httpx.request(
            "DELETE",
            f"{diary_api}/trash/{trashed['id']}",
            headers=_owner_headers(non_owner_access_token),
            json={"confirmation": "PERMANENTLY DELETE"},
        ),
    ]
    assert {
        (response.status_code, response.text)
        for response in non_owner_api_responses
    } == {(401, '{"detail":"Authentication required"}')}

    direct_calls = [
        ("list_diary_trash", {}),
        ("move_diary_entry_to_trash", {"p_entry_id": active["id"]}),
        (
            "restore_diary_entry_from_trash",
            {"p_entry_id": trashed["id"]},
        ),
        (
            "permanently_delete_diary_entry",
            {
                "p_entry_id": trashed["id"],
                "p_confirmation": "PERMANENTLY DELETE",
            },
        ),
    ]
    for function, payload in direct_calls:
        response = httpx.post(
            f"{local_supabase.api_url}/rest/v1/rpc/{function}",
            headers=_postgrest_headers(
                local_supabase,
                non_owner_access_token,
            ),
            json=payload,
        )
        assert response.status_code == 200, response.text
        assert response.json() == []

    wrong_direct_confirmation = httpx.post(
        (
            f"{local_supabase.api_url}/rest/v1/rpc/"
            "permanently_delete_diary_entry"
        ),
        headers=_postgrest_headers(local_supabase, owner_access_token),
        json={
            "p_entry_id": trashed["id"],
            "p_confirmation": "Permanently Delete",
        },
    )
    assert wrong_direct_confirmation.status_code == 400
    owner_listing = httpx.get(
        f"{diary_api}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert owner_listing.status_code == 200
    assert trashed["id"] in {
        entry["id"] for entry in owner_listing.json()["entries"]
    }

    catalog = subprocess.run(
        [
            "docker",
            "exec",
            "supabase_db_diary",
            "psql",
            "--username",
            "postgres",
            "--dbname",
            "postgres",
            "--no-align",
            "--tuples-only",
            "--command",
            (
                "select relname || ':' || relrowsecurity || ':' || "
                "relforcerowsecurity from pg_class where relname in "
                "('entries','entry_revisions','ai_processing',"
                "'entry_history_positions') order by relname;"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert set(catalog.stdout.splitlines()) == {
        "ai_processing:true:true",
        "entries:true:true",
        "entry_history_positions:true:true",
        "entry_revisions:true:true",
    }


def test_permanent_delete_requires_exact_confirmation_and_cascades(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Ticket 09 permanent deletion Revision 1.",
        entry_at="2052-03-04T08:09:10.111213+00:00",
        idempotency_key="ticket-09-permanent-deletion",
    )
    edit_response = httpx.put(
        f"{diary_api}/entries/{original['id']}/original-content",
        headers=_owner_headers(owner_access_token),
        json={
            "expected_current_revision_id": original["current_revision_id"],
            "original_content": "Ticket 09 permanent deletion Revision 2.",
        },
    )
    assert edit_response.status_code == 200, edit_response.text
    current = edit_response.json()
    revision_ids = [
        str(original["current_revision_id"]),
        str(current["current_revision_id"]),
    ]
    trash_response = httpx.post(
        f"{diary_api}/entries/{original['id']}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert trash_response.status_code == 200, trash_response.text

    endpoint = f"{diary_api}/trash/{original['id']}"
    missing_confirmation = httpx.request(
        "DELETE",
        endpoint,
        headers=_owner_headers(owner_access_token),
        json={},
    )
    wrong_case_confirmation = httpx.request(
        "DELETE",
        endpoint,
        headers=_owner_headers(owner_access_token),
        json={"confirmation": "Permanently Delete"},
    )

    assert missing_confirmation.status_code == 422
    assert wrong_case_confirmation.status_code == 422
    listing_after_failures = httpx.get(
        f"{diary_api}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert listing_after_failures.status_code == 200
    assert [
        entry["id"]
        for entry in listing_after_failures.json()["entries"]
        if entry["id"] == original["id"]
    ] == [original["id"]]

    service_headers = _service_headers(local_supabase)
    resources = {
        "entries": ("id", [str(original["id"])]),
        "entry_revisions": ("entry_id", [str(original["id"])] * 2),
        "ai_processing": ("entry_revision_id", revision_ids),
        "entry_history_positions": ("entry_id", [str(original["id"])]),
    }
    for resource, (column, expected_values) in resources.items():
        response = httpx.get(
            f"{local_supabase.api_url}/rest/v1/{resource}",
            headers=service_headers,
            params={
                "select": column,
                column: (
                    f"eq.{original['id']}"
                    if len(set(expected_values)) == 1
                    else f"in.({','.join(expected_values)})"
                ),
            },
        )
        assert response.status_code == 200, response.text
        assert sorted(row[column] for row in response.json()) == sorted(
            expected_values
        )

    delete_response = httpx.request(
        "DELETE",
        endpoint,
        headers=_owner_headers(owner_access_token),
        json={"confirmation": "PERMANENTLY DELETE"},
    )

    assert delete_response.status_code == 204, delete_response.text
    assert delete_response.content == b""
    for resource, (column, expected_values) in resources.items():
        response = httpx.get(
            f"{local_supabase.api_url}/rest/v1/{resource}",
            headers=service_headers,
            params={
                "select": column,
                column: (
                    f"eq.{original['id']}"
                    if len(set(expected_values)) == 1
                    else f"in.({','.join(expected_values)})"
                ),
            },
        )
        assert response.status_code == 200, response.text
        assert response.json() == []

    trash_listing_response = httpx.get(
        f"{diary_api}/trash",
        headers=_owner_headers(owner_access_token),
    )
    assert trash_listing_response.status_code == 200
    assert original["id"] not in {
        entry["id"] for entry in trash_listing_response.json()["entries"]
    }
