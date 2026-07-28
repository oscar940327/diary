from collections.abc import Iterable
import subprocess
from typing import Protocol

import httpx


OWNER_ID = "61c2f4ca-2fab-4b50-a0cf-12aac0ec0b24"


class SupabaseSettings(Protocol):
    api_url: str
    publishable_key: str


class PendingCapture:
    def __init__(
        self,
        *,
        original_content: str,
        entry_at: str,
        idempotency_key: str,
    ) -> None:
        self._process = subprocess.Popen(
            [
                "docker",
                "exec",
                "-i",
                "supabase_db_diary",
                "psql",
                "--username",
                "postgres",
                "--dbname",
                "postgres",
                "--no-align",
                "--tuples-only",
                "--quiet",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if self._process.stdin is None or self._process.stdout is None:
            raise AssertionError("Could not open PostgreSQL capture session")
        self._stdin = self._process.stdin
        self._stdout = self._process.stdout
        self._stdin.write(
            "begin;\n"
            "set local role authenticated;\n"
            "select set_config("
            f"'request.jwt.claim.sub', '{OWNER_ID}', true"
            ");\n"
            "select set_config("
            "'request.jwt.claim.role', 'authenticated', true"
            ");\n"
            "select 'ENTRY_ID:' || id::text "
            "from public.create_diary_entry("
            f"'{original_content}', "
            f"'{entry_at}'::timestamptz, "
            f"'{idempotency_key}'"
            ");\n"
            "\\echo CAPTURE_PENDING\n"
        )
        self._stdin.flush()
        self.entry_id = self._read_marker_value(
            value_prefix="ENTRY_ID:",
            final_marker="CAPTURE_PENDING",
        )

    def _read_marker_value(
        self,
        *,
        value_prefix: str,
        final_marker: str,
    ) -> str:
        value: str | None = None
        while True:
            line = self._stdout.readline()
            if line == "":
                stderr = (
                    self._process.stderr.read()
                    if self._process.stderr is not None
                    else ""
                )
                raise AssertionError(
                    "PostgreSQL capture session ended unexpectedly: "
                    f"{stderr}"
                )
            stripped = line.strip()
            if stripped.startswith(value_prefix):
                value = stripped.removeprefix(value_prefix)
            if stripped == final_marker:
                if value is None:
                    raise AssertionError(
                        "PostgreSQL capture did not return an Entry id"
                    )
                return value

    def commit(self) -> None:
        self._stdin.write("commit;\n\\echo CAPTURE_COMMITTED\n\\q\n")
        self._stdin.flush()
        self._read_marker_value(
            value_prefix="CAPTURE_COMMITTED",
            final_marker="CAPTURE_COMMITTED",
        )
        self._process.wait(timeout=10)

    def close(self) -> None:
        if self._process.poll() is not None:
            return
        self._stdin.write("rollback;\n\\q\n")
        self._stdin.flush()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.terminate()
            self._process.wait(timeout=10)


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


def _page_entries(
    page: dict[str, object],
) -> list[dict[str, object]]:
    groups = page["groups"]
    assert isinstance(groups, list)
    return [
        entry
        for group in groups
        for entry in group["entries"]
    ]


def _page_contents(page: dict[str, object]) -> list[object]:
    return [
        entry["original_content"]
        for entry in _page_entries(page)
    ]


def test_owner_loads_older_and_newer_history_from_a_past_anchor(
    diary_api: str,
    owner_access_token: str,
) -> None:
    _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                f"history-direction-{day}",
                f"History day {day}",
                f"2025-01-{day:02d}T12:00:00+08:00",
            )
            for day in range(1, 7)
        ),
    )

    initial_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "anchor_date": "2025-01-03",
            "limit": 2,
        },
    )

    assert initial_response.status_code == 200
    initial = initial_response.json()
    assert initial["anchor_date"] == "2025-01-03"
    assert _page_contents(initial) == [
        "History day 3",
        "History day 2",
    ]
    assert initial["older_cursor"] is not None
    assert initial["newer_cursor"] is not None

    older_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "direction": "older",
            "cursor": initial["older_cursor"],
            "limit": 2,
        },
    )
    newer_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "direction": "newer",
            "cursor": initial["newer_cursor"],
            "limit": 2,
        },
    )

    assert older_response.status_code == 200
    assert _page_contents(older_response.json()) == ["History day 1"]
    assert older_response.json()["older_cursor"] is None
    assert newer_response.status_code == 200
    assert _page_contents(newer_response.json()) == [
        "History day 5",
        "History day 4",
    ]
    assert newer_response.json()["newer_cursor"] is not None

    newest_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "direction": "newer",
            "cursor": newer_response.json()["newer_cursor"],
            "limit": 2,
        },
    )

    assert newest_response.status_code == 200
    assert "History day 6" in _page_contents(newest_response.json())


def test_history_cursor_snapshot_is_stable_for_equal_entry_times(
    diary_api: str,
    owner_access_token: str,
) -> None:
    original_entries = _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                f"history-equal-time-{index}",
                f"Equal time Entry {index}",
                "2024-12-01T09:30:00+08:00",
            )
            for index in range(4)
        ),
    )

    initial_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "anchor_date": "2024-12-01",
            "limit": 2,
        },
    )
    assert initial_response.status_code == 200
    initial = initial_response.json()

    added_after_snapshot = _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                "history-equal-time-after-snapshot",
                "Added after the cursor snapshot",
                "2024-12-01T09:30:00+08:00",
            ),
        ),
    )[0]

    older_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "direction": "older",
            "cursor": initial["older_cursor"],
            "limit": 2,
        },
    )
    assert older_response.status_code == 200

    paged_ids = [
        str(entry["id"])
        for entry in (
            _page_entries(initial)
            + _page_entries(older_response.json())
        )
    ]
    original_ids = sorted(
        (str(entry["id"]) for entry in original_entries),
        reverse=True,
    )
    assert paged_ids == original_ids
    assert str(added_after_snapshot["id"]) not in paged_ids
    assert len(paged_ids) == len(set(paged_ids))

    refreshed_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "anchor_date": "2024-12-01",
            "limit": 5,
        },
    )
    assert refreshed_response.status_code == 200
    refreshed_ids = {
        str(entry["id"])
        for entry in _page_entries(refreshed_response.json())
    }
    assert str(added_after_snapshot["id"]) in refreshed_ids


def test_history_snapshot_excludes_capture_committed_between_cursor_requests(
    diary_api: str,
    owner_access_token: str,
) -> None:
    original_entries = _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                f"history-overlap-original-{day}",
                f"Snapshot original day {day}",
                f"2099-10-{day:02d}T12:00:00+08:00",
            )
            for day in range(1, 7)
        ),
    )
    pending_capture = PendingCapture(
        idempotency_key="history-overlap-pending",
        original_content="Capture committed after the first history page",
        entry_at="2099-10-01T18:00:00+08:00",
    )
    try:
        initial_response = httpx.get(
            f"{diary_api}/entries/history",
            headers=_owner_headers(owner_access_token),
            params={
                "anchor_date": "2099-10-03",
                "limit": 2,
            },
        )
        assert initial_response.status_code == 200
        initial = initial_response.json()
        assert _page_contents(initial) == [
            "Snapshot original day 3",
            "Snapshot original day 2",
        ]

        pending_capture.commit()

        older_response = httpx.get(
            f"{diary_api}/entries/history",
            headers=_owner_headers(owner_access_token),
            params={
                "direction": "older",
                "cursor": initial["older_cursor"],
                "limit": 1,
            },
        )
        newer_response = httpx.get(
            f"{diary_api}/entries/history",
            headers=_owner_headers(owner_access_token),
            params={
                "direction": "newer",
                "cursor": initial["newer_cursor"],
                "limit": 2,
            },
        )
        assert older_response.status_code == 200
        assert newer_response.status_code == 200
        assert _page_contents(older_response.json()) == [
            "Snapshot original day 1"
        ]
        assert _page_contents(newer_response.json()) == [
            "Snapshot original day 5",
            "Snapshot original day 4",
        ]

        newest_response = httpx.get(
            f"{diary_api}/entries/history",
            headers=_owner_headers(owner_access_token),
            params={
                "direction": "newer",
                "cursor": newer_response.json()["newer_cursor"],
                "limit": 2,
            },
        )
        assert newest_response.status_code == 200
        assert _page_contents(newest_response.json()) == [
            "Snapshot original day 6"
        ]

        paged_entries = (
            _page_entries(initial)
            + _page_entries(older_response.json())
            + _page_entries(newer_response.json())
            + _page_entries(newest_response.json())
        )
        paged_ids = [str(entry["id"]) for entry in paged_entries]
        assert set(paged_ids) == {
            str(entry["id"]) for entry in original_entries
        }
        assert len(paged_ids) == len(set(paged_ids))
        assert pending_capture.entry_id not in paged_ids

        refreshed_response = httpx.get(
            f"{diary_api}/entries/history",
            headers=_owner_headers(owner_access_token),
            params={
                "anchor_date": "2099-10-03",
                "limit": 10,
            },
        )
        assert refreshed_response.status_code == 200
        assert pending_capture.entry_id in {
            str(entry["id"])
            for entry in _page_entries(refreshed_response.json())
        }
    finally:
        pending_capture.close()


def test_history_groups_complete_content_at_taipei_date_boundaries(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    _capture_entries(
        diary_api,
        owner_access_token,
        (
            (
                "history-before-taipei-midnight",
                "Complete content immediately before Taipei midnight.",
                "2025-02-01T15:59:59+00:00",
            ),
            (
                "history-at-taipei-midnight",
                "Complete content exactly at Taipei midnight.",
                "2025-02-01T16:00:00+00:00",
            ),
            (
                "history-after-taipei-midnight",
                "Complete content immediately after Taipei midnight.",
                "2025-02-01T16:00:01+00:00",
            ),
        ),
    )

    response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(owner_access_token),
        params={
            "anchor_date": "2025-02-02",
            "limit": 10,
        },
    )

    assert response.status_code == 200
    groups = response.json()["groups"]
    boundary_groups = groups[:2]
    assert [group["date"] for group in boundary_groups] == [
        "2025-02-02",
        "2025-02-01",
    ]
    assert [
        entry["original_content"]
        for entry in boundary_groups[0]["entries"]
    ] == [
        "Complete content immediately after Taipei midnight.",
        "Complete content exactly at Taipei midnight.",
    ]
    assert [
        entry["original_content"]
        for entry in boundary_groups[1]["entries"]
    ] == ["Complete content immediately before Taipei midnight."]

    non_owner_response = httpx.get(
        f"{diary_api}/entries/history",
        headers=_owner_headers(non_owner_access_token),
        params={
            "anchor_date": "2025-02-02",
            "limit": 10,
        },
    )
    assert non_owner_response.status_code == 401
    assert non_owner_response.json() == {
        "detail": "Authentication required"
    }

    non_owner_rls_response = httpx.post(
        (
            f"{local_supabase.api_url}"
            "/rest/v1/rpc/list_diary_history_v2"
        ),
        headers=_postgrest_headers(
            local_supabase,
            non_owner_access_token,
        ),
        json={
            "p_anchor_date": "2025-02-02",
            "p_direction": "initial",
            "p_cursor_entry_at": None,
            "p_cursor_entry_id": None,
            "p_snapshot": None,
            "p_limit": 10,
        },
    )
    assert non_owner_rls_response.status_code == 200
    assert non_owner_rls_response.json() == []
