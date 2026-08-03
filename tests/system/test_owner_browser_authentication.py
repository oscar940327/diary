import base64
import json
from collections.abc import Callable
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

import httpx
from playwright.sync_api import Page, Request, expect


def _history_snapshot(request_url: str) -> str | None:
    cursor_values = parse_qs(urlsplit(request_url).query).get("cursor")
    if not cursor_values:
        return None
    cursor = cursor_values[0]
    padding = "=" * (-len(cursor) % 4)
    payload = json.loads(base64.urlsafe_b64decode(cursor + padding))
    return str(payload["snapshot"])


def _capture_history_entry(
    client: httpx.Client,
    diary_api: str,
    access_token: str,
    *,
    content: str,
    entry_at: str,
    idempotency_key: str,
) -> dict[str, object]:
    response = client.post(
        f"{diary_api}/entries",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Idempotency-Key": idempotency_key,
        },
        json={
            "entry_at": entry_at,
            "original_content": content,
        },
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


def test_entry_time_change_rebuilds_loaded_history_on_one_new_snapshot(
    page: Page,
    diary_api: str,
    diary_application: str,
    owner_access_token: str,
    owner_magic_link: Callable[[], str],
) -> None:
    taipei_today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    next_month = (
        taipei_today.replace(day=28) + timedelta(days=4)
    ).replace(day=1)
    anchor_day = next_month.replace(day=5)
    dates = [
        anchor_day + timedelta(days=1),
        anchor_day,
        anchor_day - timedelta(days=1),
        anchor_day - timedelta(days=2),
        anchor_day - timedelta(days=3),
        anchor_day - timedelta(days=4),
    ]
    (
        newer_date,
        anchor_date,
        old_date,
        new_date,
        older_date,
        oldest_date,
    ) = (value.isoformat() for value in dates)
    calendar_month = anchor_date[:7]

    with httpx.Client(timeout=20) as client:
        calendar_before_response = client.get(
            f"{diary_api}/entries/calendar",
            headers={"Authorization": f"Bearer {owner_access_token}"},
            params={"month": calendar_month},
        )
        assert calendar_before_response.status_code == 200
        baseline_counts = {
            day["date"]: day["entry_count"]
            for day in calendar_before_response.json()["days"]
        }

        seeded_entries: dict[str, dict[str, object]] = {}
        for owner_date in (
            newer_date,
            anchor_date,
            old_date,
            new_date,
            older_date,
            oldest_date,
        ):
            for hour in range(20):
                content = f"Window {owner_date} hour {hour:02d}."
                seeded_entries[content] = _capture_history_entry(
                    client,
                    diary_api,
                    owner_access_token,
                    content=content,
                    entry_at=(
                        f"{owner_date}T{hour:02d}:00:00+08:00"
                    ),
                    idempotency_key=(
                        f"history-window-{owner_date}-{hour:02d}"
                    ),
                )

    moving_content = f"Window {old_date} hour 19."
    moving_entry = seeded_entries[moving_content]
    history_requests: list[str] = []

    def record_history_request(request: Request) -> None:
        url = request.url
        if urlsplit(url).path.endswith("/entries/history"):
            history_requests.append(url)

    page.on("request", record_history_request)
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{diary_application}/diary.html")
    page.get_by_label("Owner email").fill("owner@diary.test")
    page.get_by_role("button", name="Send Magic Link").click()
    expect(page.get_by_role("status")).to_contain_text("Check your email")
    page.goto(owner_magic_link())
    expect(page.get_by_text("Authenticated Diary is ready.")).to_be_visible()

    page.goto(
        f"{diary_application}/diary.html?date={anchor_date}"
    )
    expect(page.locator("article.diary-entry")).to_have_count(20)
    page.get_by_role("button", name="Load older Entries").click()
    expect(page.locator("article.diary-entry")).to_have_count(40)
    old_cursor_snapshot = next(
        snapshot
        for snapshot in (
            _history_snapshot(url) for url in history_requests
        )
        if snapshot is not None
    )

    moved_entry = page.locator(
        f"#entry-{moving_entry['id']}"
    )
    expect(moved_entry).to_be_visible()
    moved_entry.evaluate(
        "element => element.scrollIntoView({block: 'start'})"
    )
    page.wait_for_timeout(100)
    top_before = moved_entry.bounding_box()
    assert top_before is not None

    moved_entry.get_by_text("Entry actions", exact=True).click()
    moved_entry.get_by_role(
        "button",
        name="Change Entry Time",
    ).click()
    editor = page.get_by_role("dialog", name="Change Entry Time")
    editor.get_by_label("New Entry Time").fill(
        f"{new_date}T23:59"
    )
    post_change_start = len(history_requests)
    with page.expect_response(
        lambda response: (
            urlsplit(response.url).path.endswith("/entries/history")
            and "cursor" not in parse_qs(urlsplit(response.url).query)
        )
    ):
        editor.get_by_role("button", name="Save Entry Time").click()

    expect(page.locator("article.diary-entry")).to_have_count(40)
    expect(moved_entry).to_be_visible()
    top_after = moved_entry.bounding_box()
    assert top_after is not None
    assert abs(top_after["y"] - top_before["y"]) <= 8
    moved_group = moved_entry.locator("xpath=ancestor::section[1]")
    expect(
        moved_group.get_by_role("heading", name=new_date, exact=True)
    ).to_be_visible()

    rebuilt_request_urls = history_requests[post_change_start:]
    assert len(rebuilt_request_urls) == 2
    rebuilt_snapshots = {
        snapshot
        for snapshot in (
            _history_snapshot(url) for url in rebuilt_request_urls
        )
        if snapshot is not None
    }
    assert len(rebuilt_snapshots) == 1
    assert old_cursor_snapshot not in rebuilt_snapshots

    page.get_by_role("button", name="Load newer Entries").click()
    expect(page.locator("article.diary-entry")).to_have_count(60)
    page.get_by_role("button", name="Load older Entries").click()
    expect(page.locator("article.diary-entry")).to_have_count(80)

    for content in [
        *(f"Window {old_date} hour {hour:02d}." for hour in range(19)),
        *(f"Window {new_date} hour {hour:02d}." for hour in range(20)),
        moving_content,
    ]:
        expect(page.get_by_text(content, exact=True)).to_have_count(1)

    rendered_ids = page.locator("article.diary-entry").evaluate_all(
        "elements => elements.map(element => element.id)"
    )
    assert len(rendered_ids) == len(set(rendered_ids))
    assert len(rendered_ids) < len(seeded_entries)

    post_change_request_urls = history_requests[post_change_start:]
    assert len(post_change_request_urls) == 4
    assert {
        snapshot
        for snapshot in (
            _history_snapshot(url) for url in post_change_request_urls
        )
        if snapshot is not None
    } == rebuilt_snapshots
    assert all(
        int(parse_qs(urlsplit(url).query).get("limit", ["20"])[0])
        <= 20
        for url in post_change_request_urls
    )

    page.get_by_role("button", name="Calendar").click()
    expect(
        page.get_by_role("heading", name="Calendar", exact=True)
    ).to_be_visible()
    page.get_by_role("button", name="Next month").click()
    old_date_label = (
        f"{dates[2].strftime('%B')} {dates[2].day}, {dates[2].year}"
    )
    new_date_label = (
        f"{dates[3].strftime('%B')} {dates[3].day}, {dates[3].year}"
    )
    expect(
        page.get_by_role(
            "button",
            name=(
                f"{old_date_label}, "
                f"{baseline_counts.get(old_date, 0) + 19} Entries"
            ),
        )
    ).to_be_visible()
    expect(
        page.get_by_role(
            "button",
            name=(
                f"{new_date_label}, "
                f"{baseline_counts.get(new_date, 0) + 21} Entries"
            ),
        )
    ).to_be_visible()


def test_owner_completes_magic_link_on_mobile_and_reaches_diary(
    page: Page,
    diary_application: str,
    owner_magic_link: Callable[[], str],
) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{diary_application}/diary.html")

    expect(
        page.get_by_role("heading", name="Sign in to Diary")
    ).to_be_visible()
    page.get_by_label("Owner email").fill("owner@diary.test")
    page.get_by_role("button", name="Send Magic Link").click()
    expect(page.get_by_role("status")).to_contain_text(
        "Check your email"
    )

    page.goto(owner_magic_link())

    expect(
        page.get_by_role("heading", name="Diary", exact=True)
    ).to_be_visible()
    expect(
        page.get_by_text(
            "Authenticated Diary is ready.",
            exact=True,
        )
    ).to_be_visible()
    expect(
        page.get_by_role("button", name="Sign out")
    ).to_be_visible()
    expect(
        page.get_by_role("heading", name="Today")
    ).to_be_visible()

    page.get_by_role("button", name="New Entry").click()
    page.get_by_label("Original Content").fill(
        "Mobile system capture keeps the complete Original Content."
    )
    page.get_by_role("button", name="Save Entry").click()
    expect(
        page.get_by_text(
            "Mobile system capture keeps the complete Original Content.",
            exact=True,
        )
    ).to_be_visible()
    saved_entry = page.locator("article").filter(
        has_text=(
            "Mobile system capture keeps the complete Original Content."
        )
    )
    expect(
        saved_entry.get_by_text("AI processing pending")
    ).to_be_visible()

    saved_entry.get_by_text("Entry actions", exact=True).click()
    saved_entry.get_by_role(
        "button",
        name="Edit Original Content",
    ).click()
    editor = page.get_by_role("dialog", name="Edit Original Content")
    replacement = editor.get_by_label("Replacement Original Content")
    expect(replacement).to_have_value(
        "Mobile system capture keeps the complete Original Content."
    )
    replacement.fill(
        "Mobile edit saves a complete replacement as Revision 2."
    )
    editor.get_by_role("button", name="Save replacement").click()

    edited_entry = page.locator("article.diary-entry").filter(
        has_text="Mobile edit saves a complete replacement as Revision 2."
    )
    expect(edited_entry).to_be_visible()
    expect(
        edited_entry.get_by_text(
            "Mobile system capture keeps the complete Original Content.",
            exact=True,
        )
    ).not_to_be_visible()

    edited_entry.get_by_text("Entry actions", exact=True).click()
    edited_entry.get_by_role(
        "button",
        name="View revision history",
    ).click()
    revision_history = page.get_by_role("dialog", name="Revision History")
    expect(revision_history.get_by_text("Revision 2 · Current")).to_be_visible()
    expect(revision_history.get_by_text("Revision 1", exact=True)).to_be_visible()
    expect(
        revision_history.get_by_text(
            "Mobile edit saves a complete replacement as Revision 2.",
            exact=True,
        )
    ).to_be_visible()
    expect(
        revision_history.get_by_text(
            "Mobile system capture keeps the complete Original Content.",
            exact=True,
        )
    ).to_be_visible()
    expect(revision_history.locator("time")).to_have_count(2)

    revision_history.get_by_role(
        "button",
        name="Restore Revision 1",
    ).click()
    restore_confirmation = revision_history.get_by_role(
        "alertdialog",
        name="Restore Revision 1?",
    )
    expect(restore_confirmation).to_contain_text(
        "copies Revision 1 into a new Revision 3"
    )
    expect(restore_confirmation).to_contain_text(
        "Revision 1 and Revision 2 remain unchanged"
    )
    restore_confirmation.get_by_role(
        "button",
        name="Confirm restore",
    ).click()

    restored_entry = page.locator("article.diary-entry").filter(
        has_text=(
            "Mobile system capture keeps the complete Original Content."
        )
    )
    expect(restored_entry).to_be_visible()
    expect(
        restored_entry.get_by_text(
            "Mobile edit saves a complete replacement as Revision 2.",
            exact=True,
        )
    ).not_to_be_visible()

    restored_entry.get_by_text("Entry actions", exact=True).click()
    restored_entry.get_by_role(
        "button",
        name="View revision history",
    ).click()
    restored_history = page.get_by_role("dialog", name="Revision History")
    expect(
        restored_history.get_by_text("Revision 3 · Current")
    ).to_be_visible()
    expect(
        restored_history.get_by_text("Revision 2", exact=True)
    ).to_be_visible()
    expect(
        restored_history.get_by_text("Revision 1", exact=True)
    ).to_be_visible()
    expect(restored_history.locator("time")).to_have_count(3)
    restored_history.get_by_role(
        "button",
        name="Close revision history",
    ).click()

    moved_owner_date = (
        datetime.now(ZoneInfo("Asia/Taipei")) - timedelta(days=30)
    ).date().isoformat()
    captured_value = (
        restored_entry.locator("dl > div")
        .filter(has_text="Captured")
        .locator("dd")
        .inner_text()
    )
    restored_entry.get_by_text("Entry actions", exact=True).click()
    restored_entry.get_by_role(
        "button",
        name="Change Entry Time",
    ).click()
    time_editor = page.get_by_role("dialog", name="Change Entry Time")
    expect(time_editor).to_contain_text(
        "changes Entry metadata only"
    )
    expect(time_editor).to_contain_text(
        "Captured time and Original Content revisions remain unchanged"
    )
    time_editor.get_by_label("New Entry Time").fill(
        f"{moved_owner_date}T00:15"
    )
    time_editor.get_by_role("button", name="Save Entry Time").click()

    expect(
        page.get_by_role("heading", name=moved_owner_date, exact=True)
    ).to_be_visible()
    moved_entry = page.locator("article.diary-entry").filter(
        has_text=(
            "Mobile system capture keeps the complete Original Content."
        )
    )
    expect(moved_entry).to_be_visible()
    expect(
        moved_entry.locator("dl > div")
        .filter(has_text="Captured")
        .locator("dd")
    ).to_have_text(captured_value)
    expect(
        moved_entry.get_by_text("AI processing pending")
    ).to_be_visible()

    moved_entry.get_by_text("Entry actions", exact=True).click()
    moved_entry.get_by_role(
        "button",
        name="View revision history",
    ).click()
    unchanged_history = page.get_by_role(
        "dialog",
        name="Revision History",
    )
    expect(unchanged_history.locator("time")).to_have_count(3)
    unchanged_history.get_by_role(
        "button",
        name="Close revision history",
    ).click()

    page.reload()
    expect(
        page.get_by_text(
            "Authenticated Diary is ready.",
            exact=True,
        )
    ).to_be_visible()
    expect(
        page.get_by_text(
            "Mobile system capture keeps the complete Original Content.",
            exact=True,
        )
    ).to_be_visible()

    page.get_by_role("button", name="Sign out").click()
    expect(
        page.get_by_role("heading", name="Sign in to Diary")
    ).to_be_visible()
