from collections.abc import Callable

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
