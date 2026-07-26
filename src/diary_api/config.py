from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


class ConfigurationError(RuntimeError):
    pass


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name} is required")
    return value


def _exact_origin(value: str, *, name: str) -> str:
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ConfigurationError(
            f"{name} must be an exact HTTP(S) origin without a path"
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def cors_origins_from_environment() -> tuple[str, ...]:
    environment = os.environ.get("DIARY_ENVIRONMENT", "local").strip()
    if environment not in {"local", "test", "production"}:
        raise ConfigurationError(
            "DIARY_ENVIRONMENT must be local, test, or production"
        )

    local_values = os.environ.get(
        "DIARY_LOCAL_ORIGINS",
        "http://127.0.0.1:4173,http://127.0.0.1:5173",
    )
    local_origins = tuple(
        _exact_origin(value.strip(), name="DIARY_LOCAL_ORIGINS")
        for value in local_values.split(",")
        if value.strip()
    )

    production_value = os.environ.get(
        "DIARY_PRODUCTION_ORIGIN",
        "",
    ).strip()
    production_origin = (
        _exact_origin(
            production_value,
            name="DIARY_PRODUCTION_ORIGIN",
        )
        if production_value
        else None
    )

    if environment == "production":
        if production_origin is None:
            raise ConfigurationError(
                "DIARY_PRODUCTION_ORIGIN is required in production"
            )
        return (production_origin,)
    if environment == "test" and production_origin is not None:
        return (production_origin, *local_origins)
    return local_origins


@dataclass(frozen=True)
class AuthSettings:
    jwt_issuer: str
    jwt_audience: str

    @classmethod
    def from_environment(cls) -> AuthSettings:
        environment = os.environ.get(
            "DIARY_ENVIRONMENT",
            "local",
        ).strip()
        if environment not in {"local", "test", "production"}:
            raise ConfigurationError(
                "DIARY_ENVIRONMENT must be local, test, or production"
            )
        supabase_url = _required_environment("SUPABASE_URL").rstrip("/")
        issuer = os.environ.get(
            "SUPABASE_JWT_ISSUER",
            f"{supabase_url}/auth/v1",
        ).rstrip("/")
        audience = os.environ.get(
            "SUPABASE_JWT_AUDIENCE",
            "authenticated",
        ).strip()
        if not audience:
            raise ConfigurationError(
                "SUPABASE_JWT_AUDIENCE cannot be blank"
            )

        return cls(
            jwt_issuer=issuer,
            jwt_audience=audience,
        )


@dataclass(frozen=True)
class OwnerRegistrySettings:
    supabase_url: str
    secret_key: str

    @classmethod
    def from_environment(cls) -> OwnerRegistrySettings:
        return cls(
            supabase_url=_required_environment(
                "SUPABASE_URL"
            ).rstrip("/"),
            secret_key=_required_environment("SUPABASE_SECRET_KEY"),
        )
