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
    expect(page.get_by_role("status")).to_contain_text(
        "Authenticated Diary is ready"
    )
    expect(
        page.get_by_role("button", name="Sign out")
    ).to_be_visible()

    page.reload()
    expect(page.get_by_role("status")).to_contain_text(
        "Authenticated Diary is ready"
    )

    page.get_by_role("button", name="Sign out").click()
    expect(
        page.get_by_role("heading", name="Sign in to Diary")
    ).to_be_visible()
