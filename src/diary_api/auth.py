from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from diary_api.config import AuthSettings

ALLOWED_JWT_ALGORITHMS = ("ES256", "RS256", "EdDSA")
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: UUID


class SupabaseJwtVerifier:
    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings
        self._jwks = PyJWKClient(
            f"{settings.jwt_issuer}/.well-known/jwks.json",
            cache_jwk_set=True,
            lifespan=600,
            timeout=5,
        )

    async def verify(self, token: str) -> AuthenticatedIdentity:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise jwt.InvalidAlgorithmError("Unsupported JWT algorithm")

        signing_key = await asyncio.to_thread(
            self._jwks.get_signing_key_from_jwt,
            token,
        )
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience=self._settings.jwt_audience,
            issuer=self._settings.jwt_issuer,
            options={
                "require": ["aud", "exp", "iss", "sub"],
            },
        )
        return AuthenticatedIdentity(user_id=UUID(claims["sub"]))


@lru_cache
def auth_settings() -> AuthSettings:
    return AuthSettings.from_environment()


@lru_cache
def token_verifier() -> SupabaseJwtVerifier:
    return SupabaseJwtVerifier(auth_settings())


def authentication_required() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_authenticated_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthenticatedIdentity:
    if credentials is None:
        raise authentication_required()

    try:
        return await token_verifier().verify(credentials.credentials)
    except Exception as error:
        raise authentication_required() from error
