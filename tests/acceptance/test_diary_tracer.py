from playwright.sync_api import Page, expect


def test_owner_can_open_diary_and_reach_the_real_api(page: Page) -> None:
    with page.expect_response(
        lambda response: response.url.endswith("/diary-api/health")
    ) as health_response:
        page.goto("http://127.0.0.1:4173/my-personal-website/index.html")
        navigation = page.get_by_role(
            "navigation",
            name="Primary navigation",
        )
        navigation.get_by_role("link", name="DIARY", exact=True).click()

    assert health_response.value.status == 200
    assert health_response.value.json() == {
        "service": "diary-api",
        "status": "ready",
    }
    expect(page).to_have_url(
        "http://127.0.0.1:4173/my-personal-website/diary.html"
    )
    expect(page.get_by_role("status")).to_contain_text("Diary API is ready")
