from collections.abc import Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.sync_api import Page, expect


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
