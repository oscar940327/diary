from typing import Protocol

import httpx


class SupabaseSettings(Protocol):
    api_url: str
    publishable_key: str
    service_role_key: str


def _assert_protected_denial(response: httpx.Response) -> None:
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_valid_owner_token_reaches_protected_api(
    diary_api: str,
    owner_access_token: str,
) -> None:
    response = httpx.get(
        f"{diary_api}/auth/me",
        headers={"Authorization": f"Bearer {owner_access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "authenticated",
        "owner_id": "61c2f4ca-2fab-4b50-a0cf-12aac0ec0b24",
    }


def test_valid_non_owner_token_gets_the_same_protected_denial(
    diary_api: str,
    non_owner_access_token: str,
) -> None:
    response = httpx.get(
        f"{diary_api}/auth/me",
        headers={"Authorization": f"Bearer {non_owner_access_token}"},
    )

    _assert_protected_denial(response)


def test_missing_credentials_are_rejected_through_real_http(
    diary_api: str,
) -> None:
    response = httpx.get(f"{diary_api}/auth/me")

    _assert_protected_denial(response)


def test_malformed_token_is_rejected_through_real_http(
    diary_api: str,
) -> None:
    response = httpx.get(
        f"{diary_api}/auth/me",
        headers={"Authorization": "Bearer definitely-not-a-jwt"},
    )

    _assert_protected_denial(response)


def test_expired_token_is_rejected_through_real_http(
    diary_api: str,
    expired_owner_access_token: str,
) -> None:
    response = httpx.get(
        f"{diary_api}/auth/me",
        headers={
            "Authorization": f"Bearer {expired_owner_access_token}",
        },
    )

    _assert_protected_denial(response)


def test_public_signup_is_disabled(
    local_supabase: SupabaseSettings,
) -> None:
    settings = local_supabase
    response = httpx.post(
        f"{settings.api_url}/auth/v1/signup",
        headers={
            "apikey": settings.publishable_key,
            "Content-Type": "application/json",
        },
        json={
            "email": "public-signup@diary.test",
            "password": "not-a-real-secret",
        },
    )

    assert response.status_code == 422


def test_production_origin_passes_cors_preflight(
    production_diary_api: str,
) -> None:
    response = httpx.options(
        f"{production_diary_api}/auth/me",
        headers={
            "Origin": "https://oscar940327.github.io",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://oscar940327.github.io"
    )


def test_local_origin_is_configured_separately(
    diary_api: str,
) -> None:
    response = httpx.options(
        f"{diary_api}/auth/me",
        headers={
            "Origin": "http://127.0.0.1:4173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:4173"
    )


def test_production_rejects_every_unconfigured_origin(
    production_diary_api: str,
) -> None:
    for origin in (
        "http://127.0.0.1:4173",
        "https://attacker.example",
    ):
        response = httpx.options(
            f"{production_diary_api}/auth/me",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers


def test_rls_exposes_owner_configuration_only_to_the_owner(
    local_supabase: SupabaseSettings,
    owner_access_token: str,
    non_owner_access_token: str,
) -> None:
    resource_url = (
        f"{local_supabase.api_url}/rest/v1/diary_owners"
    )
    provision_response = httpx.post(
        resource_url,
        headers={
            "apikey": local_supabase.service_role_key,
            "Authorization": (
                f"Bearer {local_supabase.service_role_key}"
            ),
            "Content-Type": "application/json",
        },
        json={
            "user_id": "61c2f4ca-2fab-4b50-a0cf-12aac0ec0b24",
        },
    )
    assert provision_response.status_code == 201

    owner_response = httpx.get(
        f"{resource_url}?select=user_id",
        headers={
            "apikey": local_supabase.publishable_key,
            "Authorization": f"Bearer {owner_access_token}",
        },
    )
    non_owner_response = httpx.get(
        f"{resource_url}?select=user_id",
        headers={
            "apikey": local_supabase.publishable_key,
            "Authorization": f"Bearer {non_owner_access_token}",
        },
    )

    assert owner_response.status_code == 200
    assert owner_response.json() == [
        {
            "user_id": "61c2f4ca-2fab-4b50-a0cf-12aac0ec0b24",
        }
    ]
    assert non_owner_response.status_code == 200
    assert non_owner_response.json() == []


def test_rls_prevents_non_owner_from_mutating_owner_configuration(
    local_supabase: SupabaseSettings,
    non_owner_access_token: str,
) -> None:
    response = httpx.post(
        f"{local_supabase.api_url}/rest/v1/diary_owners",
        headers={
            "apikey": local_supabase.publishable_key,
            "Authorization": f"Bearer {non_owner_access_token}",
            "Content-Type": "application/json",
        },
        json={
            "user_id": "0c97345c-50ac-4fcb-9664-bf796b854a92",
        },
    )

    assert response.status_code == 403
