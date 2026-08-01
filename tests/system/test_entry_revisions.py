from __future__ import annotations

import httpx
from typing import Protocol, cast


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
    idempotency_key: str,
) -> dict[str, object]:
    response = httpx.post(
        f"{diary_api}/entries",
        headers={
            **_owner_headers(access_token),
            "X-Idempotency-Key": idempotency_key,
        },
        json={"original_content": content},
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


def _replace_original_content(
    diary_api: str,
    access_token: str,
    *,
    entry_id: object,
    expected_revision_id: object,
    content: str,
) -> httpx.Response:
    return httpx.put(
        f"{diary_api}/entries/{entry_id}/original-content",
        headers=_owner_headers(access_token),
        json={
            "expected_current_revision_id": expected_revision_id,
            "original_content": content,
        },
    )


def test_sequential_edits_create_immutable_revision_history(
    diary_api: str,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Ticket 06 original content.",
        idempotency_key="sequential-entry-edits",
    )

    second_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content="Ticket 06 complete replacement number two.",
    )
    assert second_response.status_code == 200, second_response.text
    second = second_response.json()
    assert second["id"] == original["id"]
    assert second["revision_number"] == 2
    assert second["current_revision_id"] != original["current_revision_id"]
    assert second["original_content"] == (
        "Ticket 06 complete replacement number two."
    )

    third_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=second["current_revision_id"],
        content="Ticket 06 complete replacement number three.",
    )
    assert third_response.status_code == 200, third_response.text
    third = third_response.json()
    assert third["revision_number"] == 3
    assert third["current_revision_id"] != second["current_revision_id"]

    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == third

    continuous_history_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={"anchor_date": third["owner_date"]},
    )
    assert continuous_history_response.status_code == 200
    current_history_entries = [
        entry
        for group in continuous_history_response.json()["groups"]
        for entry in group["entries"]
        if entry["id"] == original["id"]
    ]
    assert current_history_entries == [third]

    history_response = httpx.get(
        f"{diary_api}/entries/{original['id']}/revisions",
        headers=_owner_headers(owner_access_token),
    )
    assert history_response.status_code == 200, history_response.text
    history = history_response.json()
    assert history["entry_id"] == original["id"]
    assert history["current_revision_id"] == third["current_revision_id"]
    assert [revision["revision_number"] for revision in history["revisions"]] == [
        3,
        2,
        1,
    ]
    assert [revision["original_content"] for revision in history["revisions"]] == [
        "Ticket 06 complete replacement number three.",
        "Ticket 06 complete replacement number two.",
        "Ticket 06 original content.",
    ]
    assert [revision["is_current"] for revision in history["revisions"]] == [
        True,
        False,
        False,
    ]
    assert all(revision["created_at"] for revision in history["revisions"])


def test_stale_client_receives_current_entry_without_overwriting_it(
    diary_api: str,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Both clients opened this Original Content.",
        idempotency_key="stale-two-client-edit",
    )

    winning_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content="Client one saved the deliberate replacement.",
    )
    assert winning_response.status_code == 200, winning_response.text
    winning_entry = winning_response.json()

    stale_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content="Client two must not silently overwrite client one.",
    )

    assert stale_response.status_code == 409
    assert stale_response.json() == {
        "detail": {
            "code": "stale_entry_revision",
            "message": "Original Content changed after this editor opened.",
            "current_entry": winning_entry,
        }
    }
    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.json() == winning_entry
    history_response = httpx.get(
        f"{diary_api}/entries/{original['id']}/revisions",
        headers=_owner_headers(owner_access_token),
    )
    assert [
        revision["original_content"]
        for revision in history_response.json()["revisions"]
    ] == [
        "Client one saved the deliberate replacement.",
        "Both clients opened this Original Content.",
    ]


def test_edit_marks_old_processing_stale_and_creates_new_obligation(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Original revision requiring derived work.",
        idempotency_key="edit-processing-obligations",
    )
    edit_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content="Replacement revision requiring fresh derived work.",
    )
    assert edit_response.status_code == 200, edit_response.text
    edited = edit_response.json()

    processing_response = httpx.get(
        (
            f"{local_supabase.api_url}/rest/v1/ai_processing"
            "?select=entry_revision_id,state,draft_required,"
            "embedding_required,stale_at"
            f"&entry_revision_id=in.({original['current_revision_id']},"
            f"{edited['current_revision_id']})"
            "&order=created_at.asc"
        ),
        headers=_postgrest_headers(local_supabase, owner_access_token),
    )
    assert processing_response.status_code == 200, processing_response.text
    obligations = processing_response.json()
    assert obligations == [
        {
            "entry_revision_id": original["current_revision_id"],
            "state": "pending",
            "draft_required": True,
            "embedding_required": True,
            "stale_at": obligations[0]["stale_at"],
        },
        {
            "entry_revision_id": edited["current_revision_id"],
            "state": "pending",
            "draft_required": True,
            "embedding_required": True,
            "stale_at": None,
        },
    ]
    assert obligations[0]["stale_at"] is not None


def test_owner_cannot_patch_current_revision_pointer_directly(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="The atomic edit boundary must own this pointer.",
        idempotency_key="deny-direct-current-revision-patch",
    )
    edit_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content="Revision two must remain current.",
    )
    assert edit_response.status_code == 200, edit_response.text
    edited = edit_response.json()

    direct_patch_response = httpx.patch(
        (
            f"{local_supabase.api_url}/rest/v1/entries"
            f"?id=eq.{original['id']}"
        ),
        headers=_postgrest_headers(local_supabase, owner_access_token),
        json={"current_revision_id": original["current_revision_id"]},
    )

    assert direct_patch_response.status_code == 403
    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json() == edited


def test_owner_cannot_patch_processing_staleness_directly(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="The edit boundary must own processing staleness.",
        idempotency_key="deny-direct-processing-stale-patch",
    )
    edit_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content="Revision two creates the stale marker.",
    )
    assert edit_response.status_code == 200, edit_response.text

    direct_patch_response = httpx.patch(
        (
            f"{local_supabase.api_url}/rest/v1/ai_processing"
            f"?entry_revision_id=eq.{original['current_revision_id']}"
        ),
        headers=_postgrest_headers(local_supabase, owner_access_token),
        json={"stale_at": None},
    )

    assert direct_patch_response.status_code == 403
    processing_response = httpx.get(
        (
            f"{local_supabase.api_url}/rest/v1/ai_processing"
            "?select=stale_at"
            f"&entry_revision_id=eq.{original['current_revision_id']}"
        ),
        headers=_postgrest_headers(local_supabase, owner_access_token),
    )
    assert processing_response.status_code == 200, processing_response.text
    assert processing_response.json()[0]["stale_at"] is not None


def test_blank_edit_is_rejected_without_changing_data(
    diary_api: str,
    owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="This revision must survive a blank replacement.",
        idempotency_key="blank-entry-edit",
    )

    blank_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content=" \n\t ",
    )

    assert blank_response.status_code == 422
    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.json() == original
    history_response = httpx.get(
        f"{diary_api}/entries/{original['id']}/revisions",
        headers=_owner_headers(owner_access_token),
    )
    assert len(history_response.json()["revisions"]) == 1


def test_entry_revisions_are_owner_only_at_api_and_rls_boundaries(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="Only the owner can inspect or edit this revision.",
        idempotency_key="owner-only-entry-revisions",
    )

    denied_responses = (
        httpx.get(
            f"{diary_api}/entries/{original['id']}",
            headers=_owner_headers(non_owner_access_token),
        ),
        httpx.get(
            f"{diary_api}/entries/{original['id']}/revisions",
            headers=_owner_headers(non_owner_access_token),
        ),
        _replace_original_content(
            diary_api,
            non_owner_access_token,
            entry_id=original["id"],
            expected_revision_id=original["current_revision_id"],
            content="A non-owner must not create this replacement.",
        ),
    )
    for denied_response in denied_responses:
        assert denied_response.status_code == 401
        assert denied_response.json() == {
            "detail": "Authentication required"
        }

    revisions_response = httpx.get(
        (
            f"{local_supabase.api_url}/rest/v1/entry_revisions"
            f"?entry_id=eq.{original['id']}&select=*"
        ),
        headers=_postgrest_headers(
            local_supabase,
            non_owner_access_token,
        ),
    )
    assert revisions_response.status_code == 200
    assert revisions_response.json() == []

    denied_pointer_patch = httpx.patch(
        (
            f"{local_supabase.api_url}/rest/v1/entries"
            f"?id=eq.{original['id']}"
        ),
        headers=_postgrest_headers(local_supabase, non_owner_access_token),
        json={"current_revision_id": original["current_revision_id"]},
    )
    denied_stale_patch = httpx.patch(
        (
            f"{local_supabase.api_url}/rest/v1/ai_processing"
            f"?entry_revision_id=eq.{original['current_revision_id']}"
        ),
        headers=_postgrest_headers(local_supabase, non_owner_access_token),
        json={"stale_at": None},
    )
    assert denied_pointer_patch.status_code == 403
    assert denied_stale_patch.status_code == 403

    direct_edit_response = httpx.post(
        (
            f"{local_supabase.api_url}/rest/v1/rpc/"
            "edit_diary_entry_original_content"
        ),
        headers=_postgrest_headers(
            local_supabase,
            non_owner_access_token,
        ),
        json={
            "p_entry_id": original["id"],
            "p_expected_current_revision_id": (
                original["current_revision_id"]
            ),
            "p_original_content": "RLS must reject this replacement.",
        },
    )
    assert direct_edit_response.status_code == 200
    assert direct_edit_response.json() == []


def test_fastapi_edit_uses_owner_token_for_postgres_rls(
    diary_api: str,
    owner_access_token: str,
    entry_update_rls_denial: None,
) -> None:
    original = _capture_entry(
        diary_api,
        owner_access_token,
        content="RLS must preserve this current revision.",
        idempotency_key="edit-rls-defense",
    )

    denied_response = _replace_original_content(
        diary_api,
        owner_access_token,
        entry_id=original["id"],
        expected_revision_id=original["current_revision_id"],
        content="This transaction must roll back at the RLS boundary.",
    )

    assert denied_response.status_code == 503
    detail_response = httpx.get(
        f"{diary_api}/entries/{original['id']}",
        headers=_owner_headers(owner_access_token),
    )
    assert detail_response.json() == original
    history_response = httpx.get(
        f"{diary_api}/entries/{original['id']}/revisions",
        headers=_owner_headers(owner_access_token),
    )
    assert len(history_response.json()["revisions"]) == 1
