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
from jwt.exceptions import (
    InvalidTokenError,
    PyJWKClientConnectionError,
    PyJWKClientError,
    PyJWKSetError,
)

from diary_api.config import AuthSettings

ALLOWED_JWT_ALGORITHMS = ("ES256", "RS256", "EdDSA")
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: UUID


class InvalidAuthenticationToken(Exception):
    pass


class AuthenticationServiceUnavailable(Exception):
    pass


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
        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as error:
            raise InvalidAuthenticationToken from error

        algorithm = header.get("alg")
        if algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise InvalidAuthenticationToken

        try:
            signing_key = await asyncio.to_thread(
                self._jwks.get_signing_key_from_jwt,
                token,
            )
        except (PyJWKClientConnectionError, PyJWKSetError) as error:
            raise AuthenticationServiceUnavailable from error
        except PyJWKClientError as error:
            raise InvalidAuthenticationToken from error

        try:
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
        except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
            raise InvalidAuthenticationToken from error


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


def authentication_service_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication service unavailable",
    )


async def require_authenticated_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthenticatedIdentity:
    if credentials is None:
        raise authentication_required()

    try:
        return await token_verifier().verify(credentials.credentials)
    except InvalidAuthenticationToken as error:
        raise authentication_required() from error
    except AuthenticationServiceUnavailable as error:
        raise authentication_service_unavailable() from error
