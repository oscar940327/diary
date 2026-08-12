from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Protocol, cast
from uuid import UUID

import httpx
import jwt


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_SCHEMA_VERSION = "20260805120000"
HISTORY_POSITION_PREVIOUS_SCHEMA_VERSION = "20260803120000"
MIGRATION_PAUSE_LOCK = 808_041_200
CREATE_PAUSE_LOCK = 808_041_201
TRANSFORMATION_MIGRATION = (
    REPOSITORY_ROOT
    / "supabase"
    / "migrations"
    / "20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql"
)
OWNER_ID = UUID("61c2f4ca-2fab-4b50-a0cf-12aac0ec0b24")
NON_OWNER_ID = UUID("0c97345c-50ac-4fcb-9664-bf796b854a92")


class SupabaseSettings(Protocol):
    api_url: str
    publishable_key: str
    service_role_key: str


def _supabase_executable() -> str:
    executable_name = "supabase.cmd" if os.name == "nt" else "supabase"
    return str(REPOSITORY_ROOT / "node_modules" / ".bin" / executable_name)


def _supabase_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_supabase_executable(), *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _psql(statement: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "docker",
            "exec",
            "--interactive",
            "supabase_db_diary",
            "psql",
            "--username",
            "postgres",
            "--dbname",
            "postgres",
            "--set",
            "ON_ERROR_STOP=1",
        ],
        input=statement,
        check=False,
        capture_output=True,
        text=True,
    )


def _open_psql() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            "docker",
            "exec",
            "--interactive",
            "supabase_db_diary",
            "psql",
            "--username",
            "postgres",
            "--dbname",
            "postgres",
            "--set",
            "ON_ERROR_STOP=1",
        ],
        cwd=REPOSITORY_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _start_migration_upgrade() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [_supabase_executable(), "migration", "up", "--local"],
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for_database_condition(
    statement: str,
    *,
    timeout_seconds: float = 15,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_result = "database condition was not queried"
    while time.monotonic() < deadline:
        result = _psql(statement)
        last_result = f"stdout={result.stdout!r} stderr={result.stderr!r}"
        if _database_condition_is_true(result):
            return
        time.sleep(0.05)
    raise AssertionError(last_result)


def _database_condition_is_true(
    result: subprocess.CompletedProcess[str],
) -> bool:
    return result.returncode == 0 and any(
        line.strip() == "1" for line in result.stdout.splitlines()
    )


def _stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.kill()
    process.communicate(timeout=10)


def _owner_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _postgrest_headers(
    settings: SupabaseSettings,
    access_token: str,
) -> dict[str, str]:
    return {
        "apikey": settings.publishable_key,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _admin_headers(settings: SupabaseSettings) -> dict[str, str]:
    return {
        "apikey": settings.service_role_key,
        "Authorization": f"Bearer {settings.service_role_key}",
        "Content-Type": "application/json",
    }


def _create_owner_registry(settings: SupabaseSettings) -> None:
    deadline = time.monotonic() + 10
    last_result = "owner registry did not respond"
    while time.monotonic() < deadline:
        response = httpx.post(
            f"{settings.api_url}/rest/v1/diary_owners",
            headers=_admin_headers(settings),
            json={"user_id": str(OWNER_ID)},
            timeout=10,
        )
        rows = httpx.get(
            f"{settings.api_url}/rest/v1/diary_owners",
            headers=_admin_headers(settings),
            params={"select": "user_id"},
            timeout=10,
        )
        if rows.status_code == 200 and rows.json() == [
            {"user_id": str(OWNER_ID)}
        ]:
            return
        last_result = (
            f"POST {response.status_code} {response.text}; "
            f"GET {rows.status_code} {rows.text}"
        )
        time.sleep(0.1)
    raise AssertionError(last_result)


def _assert_owner_registry(
    settings: SupabaseSettings,
    access_token: str,
) -> None:
    claims = jwt.decode(
        access_token,
        options={"verify_signature": False},
    )
    assert claims["sub"] == str(OWNER_ID)
    for actor, headers in (
        ("service role", _admin_headers(settings)),
        ("owner", _postgrest_headers(settings, access_token)),
    ):
        response = httpx.get(
            f"{settings.api_url}/rest/v1/diary_owners",
            headers=headers,
            params={"select": "user_id"},
            timeout=10,
        )
        assert response.status_code == 200, f"{actor}: {response.text}"
        assert response.json() == [
            {"user_id": str(OWNER_ID)}
        ], actor


def _restore_auth_users(settings: SupabaseSettings) -> None:
    for user_id, email in (
        (OWNER_ID, "owner@diary.test"),
        (NON_OWNER_ID, "not-owner@diary.test"),
    ):
        response = httpx.post(
            f"{settings.api_url}/auth/v1/admin/users",
            headers=_admin_headers(settings),
            json={
                "id": str(user_id),
                "email": email,
                "email_confirm": True,
            },
            timeout=10,
        )
        assert response.status_code in {200, 422}, response.text


def _rpc_create(
    settings: SupabaseSettings,
    access_token: str,
    *,
    content: str,
    entry_at: str,
    idempotency_key: str,
) -> dict[str, object]:
    response = httpx.post(
        f"{settings.api_url}/rest/v1/rpc/create_diary_entry",
        headers=_postgrest_headers(settings, access_token),
        json={
            "p_original_content": content,
            "p_entry_at": entry_at,
            "p_idempotency_key": idempotency_key,
        },
        timeout=10,
    )
    assert response.status_code == 200, response.text
    rows = cast(list[dict[str, object]], response.json())
    assert len(rows) == 1
    return rows[0]


def _rows(
    settings: SupabaseSettings,
    access_token: str,
    table: str,
    select: str,
    *,
    order: str,
) -> list[dict[str, object]]:
    response = httpx.get(
        f"{settings.api_url}/rest/v1/{table}",
        headers=_postgrest_headers(settings, access_token),
        params={"select": select, "order": order},
        timeout=10,
    )
    assert response.status_code == 200, response.text
    return cast(list[dict[str, object]], response.json())


def test_previous_version_create_committing_during_history_upgrade_gets_initial_position(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
) -> None:
    reset_previous = _supabase_cli(
        "db",
        "reset",
        "--local",
        "--version",
        HISTORY_POSITION_PREVIOUS_SCHEMA_VERSION,
    )
    assert reset_previous.returncode == 0, reset_previous.stderr

    lock_controller: subprocess.Popen[str] | None = None
    previous_create: subprocess.Popen[str] | None = None
    upgrade: subprocess.Popen[str] | None = None
    try:
        _restore_auth_users(local_supabase)
        _create_owner_registry(local_supabase)
        _assert_owner_registry(
            local_supabase,
            owner_access_token,
        )

        pause_migration = _psql(
            f"""
            create function public.ticket08_pause_history_upgrade()
            returns event_trigger
            language plpgsql
            as $$
            begin
                if current_query() ilike
                    '%entry_history_positions_one_current_idx%'
                then
                    perform pg_advisory_xact_lock({MIGRATION_PAUSE_LOCK});
                end if;
            end;
            $$;

            create event trigger ticket08_pause_history_upgrade
            on ddl_command_start
            when tag in ('CREATE INDEX')
            execute function public.ticket08_pause_history_upgrade();
            """
        )
        assert pause_migration.returncode == 0, pause_migration.stderr

        lock_controller = _open_psql()
        assert lock_controller.stdin is not None
        lock_controller.stdin.write(
            "set application_name = 'ticket08_lock_controller';\n"
            f"select pg_advisory_lock({MIGRATION_PAUSE_LOCK});\n"
            f"select pg_advisory_lock({CREATE_PAUSE_LOCK});\n"
        )
        lock_controller.stdin.flush()
        _wait_for_database_condition(
            f"""
            select (count(*) = 2)::integer
            from pg_catalog.pg_locks
            join pg_catalog.pg_stat_activity
              on pg_stat_activity.pid = pg_locks.pid
            where pg_stat_activity.application_name =
                    'ticket08_lock_controller'
              and pg_locks.locktype = 'advisory'
              and pg_locks.objid in (
                    {MIGRATION_PAUSE_LOCK},
                    {CREATE_PAUSE_LOCK}
              )
              and pg_locks.granted;
            """
        )

        upgrade = _start_migration_upgrade()
        _wait_for_database_condition(
            f"""
            select count(*)
            from pg_catalog.pg_locks
            where pg_locks.locktype = 'advisory'
              and pg_locks.objid = {MIGRATION_PAUSE_LOCK}
              and not pg_locks.granted;
            """
        )

        previous_create = _open_psql()
        assert previous_create.stdin is not None
        previous_create.stdin.write(
            "begin;\n"
            "set application_name = 'ticket08_previous_create';\n"
            "set local role authenticated;\n"
            "select set_config(\n"
            "  'request.jwt.claims',\n"
            f"  '{{\"sub\":\"{OWNER_ID}\",\"role\":\"authenticated\"}}',\n"
            "  true\n"
            ");\n"
            "select id from public.create_diary_entry(\n"
            "  'Concurrent previous-version Create.',\n"
            "  '2088-03-04T05:06:07.123456+08:00'::timestamptz,\n"
            "  'upgrade-concurrent-create'\n"
            ");\n"
            f"select pg_advisory_lock({CREATE_PAUSE_LOCK});\n"
            "commit;\n"
            "\\q\n"
        )
        previous_create.stdin.flush()

        _wait_for_database_condition(
            f"""
            select (
                exists (
                    select 1
                    from pg_catalog.pg_locks
                    join pg_catalog.pg_stat_activity
                      on pg_stat_activity.pid = pg_locks.pid
                    where pg_stat_activity.application_name =
                            'ticket08_previous_create'
                      and pg_locks.locktype = 'advisory'
                      and pg_locks.objid = {CREATE_PAUSE_LOCK}
                      and not pg_locks.granted
                )
                or exists (
                    select 1
                    from pg_catalog.pg_locks
                    join pg_catalog.pg_stat_activity
                      on pg_stat_activity.pid = pg_locks.pid
                    where pg_stat_activity.application_name =
                            'ticket08_previous_create'
                      and pg_locks.relation = 'public.entries'::regclass
                      and pg_locks.mode = 'RowExclusiveLock'
                      and not pg_locks.granted
                )
            )::integer;
            """
        )

        create_reached_upgrade_gap = _database_condition_is_true(
            _psql(
                f"""
                select count(*)
                from pg_catalog.pg_locks
                join pg_catalog.pg_stat_activity
                  on pg_stat_activity.pid = pg_locks.pid
                where pg_stat_activity.application_name =
                        'ticket08_previous_create'
                  and pg_locks.locktype = 'advisory'
                  and pg_locks.objid = {CREATE_PAUSE_LOCK}
                  and not pg_locks.granted;
                """
            )
        )

        lock_controller.stdin.write(
            f"select pg_advisory_unlock({CREATE_PAUSE_LOCK});\n"
        )
        lock_controller.stdin.flush()
        if create_reached_upgrade_gap:
            previous_create_stdout, previous_create_stderr = (
                previous_create.communicate(timeout=30)
            )
            assert previous_create.returncode == 0, (
                previous_create_stdout,
                previous_create_stderr,
            )

        lock_controller.stdin.write(
            f"select pg_advisory_unlock({MIGRATION_PAUSE_LOCK});\n"
        )
        lock_controller.stdin.flush()

        upgrade_stdout, upgrade_stderr = upgrade.communicate(timeout=120)
        assert upgrade.returncode == 0, (upgrade_stdout, upgrade_stderr)
        if not create_reached_upgrade_gap:
            previous_create_stdout, previous_create_stderr = (
                previous_create.communicate(timeout=30)
            )
            assert previous_create.returncode == 0, (
                previous_create_stdout,
                previous_create_stderr,
            )

        no_pause_trigger = _psql(
            """
            drop event trigger ticket08_pause_history_upgrade;
            drop function public.ticket08_pause_history_upgrade();
            """
        )
        assert no_pause_trigger.returncode == 0, no_pause_trigger.stderr

        _wait_for_database_condition(
            """
            select (count(*) = 0)::integer
            from pg_catalog.pg_locks
            join pg_catalog.pg_stat_activity
              on pg_stat_activity.pid = pg_locks.pid
            where pg_stat_activity.application_name =
                    'ticket08_previous_create';
            """
        )

        created_entries = _rows(
            local_supabase,
            owner_access_token,
            "entries",
            "id,entry_at,idempotency_key,current_revision_id,created_at",
            order="id.asc",
        )
        concurrent_entry = next(
            entry
            for entry in created_entries
            if entry["idempotency_key"] == "upgrade-concurrent-create"
        )
        concurrent_entry_id = cast(str, concurrent_entry["id"])

        history = httpx.get(
            f"{diary_api}/entries/history",
            headers=_owner_headers(owner_access_token),
            params={"anchor_date": "2088-03-04", "limit": 50},
            timeout=10,
        )
        assert history.status_code == 200, history.text
        history_ids = [
            entry["id"]
            for group in history.json()["groups"]
            for entry in group["entries"]
        ]
        assert history_ids.count(concurrent_entry_id) == 1

        positions = _rows(
            local_supabase,
            owner_access_token,
            "entry_history_positions",
            "entry_id,entry_at,valid_from_xid,valid_until_xid",
            order="entry_id.asc,valid_from_xid.asc",
        )
        current_positions = [
            position
            for position in positions
            if position["entry_id"] == concurrent_entry_id
            and position["valid_until_xid"] is None
        ]
        assert len(current_positions) == 1
        assert current_positions[0]["entry_at"] == (
            "2088-03-03T21:06:07.123456+00:00"
        )

        change = httpx.post(
            (
                f"{local_supabase.api_url}/rest/v1/rpc/"
                "change_diary_entry_time"
            ),
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
            json={
                "p_entry_id": concurrent_entry_id,
                "p_entry_at": "2088-03-05T06:07:08.654321+08:00",
            },
            timeout=10,
        )
        assert change.status_code == 200, change.text
        changed_rows = cast(list[dict[str, object]], change.json())
        assert len(changed_rows) == 1
        assert changed_rows[0]["id"] == concurrent_entry_id
    finally:
        _stop_process(previous_create)
        _stop_process(upgrade)
        _stop_process(lock_controller)
        restore = _supabase_cli("db", "reset", "--local")
        assert restore.returncode == 0, restore.stderr
        _restore_auth_users(local_supabase)
        _create_owner_registry(local_supabase)


def test_ordered_upgrade_transforms_unsafe_entry_times_with_immutable_audit(
    diary_api: str,
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    reset_previous = _supabase_cli(
        "db",
        "reset",
        "--local",
        "--version",
        PREVIOUS_SCHEMA_VERSION,
    )
    assert reset_previous.returncode == 0, reset_previous.stderr

    try:
        _restore_auth_users(local_supabase)
        _create_owner_registry(local_supabase)
        _assert_owner_registry(local_supabase, owner_access_token)
        unsafe_first = _rpc_create(
            local_supabase,
            owner_access_token,
            content="First preceding-version-valid unsafe Entry.",
            entry_at="9999-12-31T16:00:00Z",
            idempotency_key="upgrade-unsafe-first",
        )
        unsafe_second = _rpc_create(
            local_supabase,
            owner_access_token,
            content="Second preceding-version-valid unsafe Entry.",
            entry_at="9999-12-31T23:59:59.999999Z",
            idempotency_key="upgrade-unsafe-second",
        )
        safe_entry = _rpc_create(
            local_supabase,
            owner_access_token,
            content="Safe Entry must not be transformed.",
            entry_at="2088-01-02T03:04:05.123456Z",
            idempotency_key="upgrade-safe-control",
        )

        entry_select = (
            "id,owner_id,entry_at,idempotency_key,current_revision_id,"
            "history_membership_xid,created_at,updated_at,trashed_at"
        )
        revision_select = (
            "id,entry_id,revision_number,original_content,created_at"
        )
        processing_select = (
            "id,entry_revision_id,state,draft_required,embedding_required,"
            "attempt_count,created_at,updated_at,stale_at"
        )
        position_select = (
            "entry_id,entry_at,valid_from_xid,valid_until_xid"
        )
        entries_before = _rows(
            local_supabase,
            owner_access_token,
            "entries",
            entry_select,
            order="id.asc",
        )
        revisions_before = _rows(
            local_supabase,
            owner_access_token,
            "entry_revisions",
            revision_select,
            order="id.asc",
        )
        processing_before = _rows(
            local_supabase,
            owner_access_token,
            "ai_processing",
            processing_select,
            order="id.asc",
        )
        positions_before = _rows(
            local_supabase,
            owner_access_token,
            "entry_history_positions",
            position_select,
            order="entry_id.asc,valid_from_xid.asc",
        )

        upgrade = _supabase_cli("migration", "up", "--local")
        assert upgrade.returncode == 0, upgrade.stderr

        entries_after = _rows(
            local_supabase,
            owner_access_token,
            "entries",
            entry_select,
            order="id.asc",
        )
        revisions_after = _rows(
            local_supabase,
            owner_access_token,
            "entry_revisions",
            revision_select,
            order="id.asc",
        )
        processing_after = _rows(
            local_supabase,
            owner_access_token,
            "ai_processing",
            processing_select,
            order="id.asc",
        )
        positions_after = _rows(
            local_supabase,
            owner_access_token,
            "entry_history_positions",
            position_select,
            order="entry_id.asc,valid_from_xid.asc",
        )
        audits = _rows(
            local_supabase,
            owner_access_token,
            "entry_time_migration_audits",
            (
                "entry_id,owner_id,original_entry_at,transformed_entry_at,"
                "transformation_reason,migration_version,migrated_at"
            ),
            order="entry_id.asc",
        )

        assert revisions_after == revisions_before
        assert processing_after == processing_before
        assert len(entries_after) == len(entries_before) == 3
        assert len(audits) == 2

        before_by_id = {row["id"]: row for row in entries_before}
        after_by_id = {row["id"]: row for row in entries_after}
        expected_times = {
            unsafe_first["id"]: (
                "9999-12-31T16:00:00+00:00",
                "9999-12-30T16:00:00+00:00",
            ),
            unsafe_second["id"]: (
                "9999-12-31T23:59:59.999999+00:00",
                "9999-12-30T23:59:59.999999+00:00",
            ),
        }
        for entry_id, (original, transformed) in expected_times.items():
            before = before_by_id[entry_id]
            after = after_by_id[entry_id]
            assert before["entry_at"] == original
            assert after == {**before, "entry_at": transformed}

        assert after_by_id[safe_entry["id"]] == before_by_id[safe_entry["id"]]
        audit_by_id = {row["entry_id"]: row for row in audits}
        for entry_id, (original, transformed) in expected_times.items():
            audit = audit_by_id[entry_id]
            assert audit["owner_id"] == str(OWNER_ID)
            assert audit["original_entry_at"] == original
            assert audit["transformed_entry_at"] == transformed
            assert audit["transformation_reason"] == (
                "Taipei-safe upper-bound remediation: active Entry Time "
                "shifted exactly 24 hours earlier"
            )
            assert audit["migration_version"] == "20260807120000"
            assert audit["migrated_at"] is not None

        unsafe_ids = set(expected_times)
        order_before = [
            row["id"]
            for row in sorted(
                (
                    row
                    for row in entries_before
                    if row["id"] in unsafe_ids
                ),
                key=lambda row: cast(str, row["entry_at"]),
                reverse=True,
            )
        ]
        order_after = [
            row["id"]
            for row in sorted(
                (
                    row
                    for row in entries_after
                    if row["id"] in unsafe_ids
                ),
                key=lambda row: cast(str, row["entry_at"]),
                reverse=True,
            )
        ]
        assert order_after == order_before

        before_positions = {
            (row["entry_id"], row["entry_at"], row["valid_from_xid"])
            for row in positions_before
        }
        after_positions = {
            (row["entry_id"], row["entry_at"], row["valid_from_xid"])
            for row in positions_after
        }
        assert before_positions <= after_positions
        for entry_id, (_, transformed) in expected_times.items():
            current_positions = [
                row
                for row in positions_after
                if row["entry_id"] == entry_id
                and row["valid_until_xid"] is None
            ]
            assert len(current_positions) == 1
            assert current_positions[0]["entry_at"] == transformed

        for entry_id, (_, transformed) in expected_times.items():
            detail = httpx.get(
                f"{diary_api}/entries/{entry_id}",
                headers=_owner_headers(owner_access_token),
                timeout=10,
            )
            assert detail.status_code == 200, detail.text
            assert detail.json()["entry_at"] == transformed.replace(
                "+00:00",
                "Z",
            )

        history = httpx.get(
            f"{diary_api}/entries/history",
            headers=_owner_headers(owner_access_token),
            params={"anchor_date": "9999-12-31", "limit": 50},
            timeout=10,
        )
        assert history.status_code == 200, history.text
        history_ids = [
            entry["id"]
            for group in history.json()["groups"]
            for entry in group["entries"]
        ]
        assert history_ids.count(unsafe_first["id"]) == 1
        assert history_ids.count(unsafe_second["id"]) == 1

        calendar = httpx.get(
            f"{diary_api}/entries/calendar",
            headers=_owner_headers(owner_access_token),
            params={"month": "9999-12"},
            timeout=10,
        )
        assert calendar.status_code == 200, calendar.text
        counts = {
            day["date"]: day["entry_count"]
            for day in calendar.json()["days"]
        }
        assert counts["9999-12-31"] == 2

        non_owner_audits = httpx.get(
            (
                f"{local_supabase.api_url}/rest/v1/"
                "entry_time_migration_audits"
            ),
            headers=_postgrest_headers(
                local_supabase,
                non_owner_access_token,
            ),
            timeout=10,
        )
        assert non_owner_audits.status_code == 200, non_owner_audits.text
        assert non_owner_audits.json() == []

        unauthorized = httpx.get(
            (
                f"{local_supabase.api_url}/rest/v1/"
                "entry_time_migration_audits"
            ),
            headers={"apikey": local_supabase.publishable_key},
            timeout=10,
        )
        assert unauthorized.status_code in {401, 403}

        audit_patch = httpx.patch(
            (
                f"{local_supabase.api_url}/rest/v1/"
                "entry_time_migration_audits"
                f"?entry_id=eq.{unsafe_first['id']}"
            ),
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
            json={"transformation_reason": "overwritten"},
            timeout=10,
        )
        assert audit_patch.status_code == 403

        repeat = _psql(TRANSFORMATION_MIGRATION.read_text(encoding="utf-8"))
        assert repeat.returncode == 0, repeat.stderr
        assert _rows(
            local_supabase,
            owner_access_token,
            "entries",
            entry_select,
            order="id.asc",
        ) == entries_after
        assert _rows(
            local_supabase,
            owner_access_token,
            "entry_revisions",
            revision_select,
            order="id.asc",
        ) == revisions_after
        assert _rows(
            local_supabase,
            owner_access_token,
            "ai_processing",
            processing_select,
            order="id.asc",
        ) == processing_after
        assert _rows(
            local_supabase,
            owner_access_token,
            "entry_history_positions",
            position_select,
            order="entry_id.asc,valid_from_xid.asc",
        ) == positions_after
        assert _rows(
            local_supabase,
            owner_access_token,
            "entry_time_migration_audits",
            (
                "entry_id,owner_id,original_entry_at,transformed_entry_at,"
                "transformation_reason,migration_version,migrated_at"
            ),
            order="entry_id.asc",
        ) == audits

        rollback_create = _rpc_create(
            local_supabase,
            owner_access_token,
            content="Previous application Create contract remains usable.",
            entry_at="2088-02-03T04:05:06.123456+08:00",
            idempotency_key="upgrade-rollback-create",
        )
        assert set(rollback_create) == {
            "id",
            "current_revision_id",
            "revision_number",
            "original_content",
            "entry_at",
            "created_at",
            "owner_date",
            "processing_state",
            "was_created",
        }
        rollback_change = httpx.post(
            (
                f"{local_supabase.api_url}/rest/v1/rpc/"
                "change_diary_entry_time"
            ),
            headers=_postgrest_headers(
                local_supabase,
                owner_access_token,
            ),
            json={
                "p_entry_id": rollback_create["id"],
                "p_entry_at": "2088-02-04T05:06:07.654321+08:00",
            },
            timeout=10,
        )
        assert rollback_change.status_code == 200, rollback_change.text
        changed_rows = cast(
            list[dict[str, object]],
            rollback_change.json(),
        )
        assert len(changed_rows) == 1
        assert set(changed_rows[0]) == {
            "id",
            "current_revision_id",
            "revision_number",
            "original_content",
            "entry_at",
            "created_at",
            "owner_date",
            "processing_state",
        }
        rollback_detail = httpx.get(
            f"{diary_api}/entries/{rollback_create['id']}",
            headers=_owner_headers(owner_access_token),
            timeout=10,
        )
        assert rollback_detail.status_code == 200, rollback_detail.text
        assert rollback_detail.json()["owner_date"] == "2088-02-04"
    finally:
        restore = _supabase_cli("db", "reset", "--local")
        assert restore.returncode == 0, restore.stderr
        _restore_auth_users(local_supabase)
        _create_owner_registry(local_supabase)
