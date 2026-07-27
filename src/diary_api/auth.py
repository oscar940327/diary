from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from functools import lru_cache
from http.client import HTTPException as HttpClientException
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWK, PyJWKClient
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
    access_token: str = field(repr=False)


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

        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise InvalidAuthenticationToken

        signing_keys = await self._get_signing_keys()
        signing_key = self._jwks.match_kid(signing_keys, kid)
        if signing_key is None:
            refreshed_signing_keys = await self._get_signing_keys(
                refresh=True
            )
            signing_key = self._jwks.match_kid(
                refreshed_signing_keys,
                kid,
            )
        if signing_key is None:
            raise InvalidAuthenticationToken

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
            return AuthenticatedIdentity(
                user_id=UUID(claims["sub"]),
                access_token=token,
            )
        except (
            InvalidTokenError,
            KeyError,
            OverflowError,
            TypeError,
            ValueError,
        ) as error:
            raise InvalidAuthenticationToken from error

    async def _get_signing_keys(
        self,
        *,
        refresh: bool = False,
    ) -> list[PyJWK]:
        try:
            signing_keys = await asyncio.to_thread(
                self._jwks.get_signing_keys,
                refresh,
            )
            if any(
                not isinstance(key.key_id, str) or not key.key_id
                for key in signing_keys
            ):
                raise AuthenticationServiceUnavailable
            return signing_keys
        except (
            AttributeError,
            HttpClientException,
            OSError,
            PyJWKClientConnectionError,
            PyJWKClientError,
            PyJWKSetError,
            TypeError,
            ValueError,
        ) as error:
            raise AuthenticationServiceUnavailable from error


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
