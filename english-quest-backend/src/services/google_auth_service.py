"""Google Sign-In (Google Identity Services) backend support.

The browser obtains a signed ID token ("credential") from Google and posts it to
``POST /auth/google``. We verify the token cryptographically against Google's
public JWKS, then find, link or create the matching local user and issue our own
JWT — exactly the same token the password login returns.

Only ``GOOGLE_CLIENT_ID`` is required (no client secret): the ID-token flow never
needs one, because verification is done with Google's public keys.
"""

from functools import lru_cache

import jwt
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.settings import settings
from src.models.models import Role, User
from src.services.account_service import serialize_user
from src.services.security import create_access_token
from src.services.user_lookup import get_user_with_role

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": []},
    )


@lru_cache(maxsize=1)
def _jwks_client() -> jwt.PyJWKClient:
    """One shared JWKS client so Google's signing keys are cached in memory."""
    return jwt.PyJWKClient(GOOGLE_JWKS_URL)


def verify_google_credential(credential: str) -> dict:
    """Validate a Google ID token and return its claims.

    Checks the RS256 signature (Google JWKS), audience (our client ID), issuer
    and expiry. Raises a 401/503 HTTPException on any failure.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise _error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "GOOGLE_NOT_CONFIGURED",
            "Google Sign-In is not configured on this server",
        )

    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(credential)
    except Exception as exc:  # network/JWKS/malformed-token failures
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "GOOGLE_TOKEN_INVALID",
            "Could not verify the Google token",
        ) from exc

    try:
        claims = jwt.decode(
            credential,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID,
            issuer=list(GOOGLE_ISSUERS),
            options={"require": ["exp", "iat", "sub", "aud", "iss", "email"]},
        )
    except jwt.PyJWTError as exc:
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "GOOGLE_TOKEN_INVALID",
            "Invalid or expired Google token",
        ) from exc

    # Google returns a boolean, but older tokens used the string "true".
    if str(claims.get("email_verified", "")).lower() != "true":
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "GOOGLE_EMAIL_UNVERIFIED",
            "Google account email is not verified",
        )

    if not claims.get("email"):
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "GOOGLE_EMAIL_MISSING",
            "Google account does not expose an email address",
        )

    return claims


async def _student_role(db: AsyncSession) -> Role:
    result = await db.execute(select(Role).where(Role.name == "student"))
    role = result.scalar_one_or_none()
    if role is None:
        raise _error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "ROLE_MISSING",
            "Default role 'student' is not seeded",
        )
    return role


def _names_from_claims(claims: dict) -> tuple[str, str]:
    given = (claims.get("given_name") or "").strip()
    family = (claims.get("family_name") or "").strip()

    if not given and not family:
        full = (claims.get("name") or "").strip()
        if full:
            head, _, tail = full.partition(" ")
            given, family = head, tail.strip()

    if not given:
        given = (claims.get("email") or "Learner").split("@")[0]

    # first_name/last_name are NOT NULL in the schema, so keep them strings.
    return given[:100], family[:100]


async def _find_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.google_id == google_id)
    )
    return result.scalar_one_or_none()


async def _find_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(func.lower(User.email) == email.lower())
    )
    return result.scalar_one_or_none()


async def login_with_google(db: AsyncSession, credential: str) -> dict:
    """Authenticate (or register) a user from a Google ID token."""
    claims = verify_google_credential(credential)
    google_id = str(claims["sub"])
    email = str(claims["email"]).strip().lower()
    first_name, last_name = _names_from_claims(claims)

    # 1) Returning Google user.
    user = await _find_by_google_id(db, google_id)
    is_new_user = False

    # 2) Existing password account with the same verified email: link it, so the
    #    user keeps their XP and progress instead of getting a duplicate account.
    if user is None:
        user = await _find_by_email(db, email)
        if user is not None:
            if user.google_id and user.google_id != google_id:
                raise _error(
                    status.HTTP_409_CONFLICT,
                    "GOOGLE_ACCOUNT_CONFLICT",
                    "This email is already linked to a different Google account",
                )
            user.google_id = google_id
            if user.password_hash is None and user.email != email:
                user.email = email
            try:
                await db.commit()
            except IntegrityError as exc:
                await db.rollback()
                raise _error(
                    status.HTTP_409_CONFLICT,
                    "EMAIL_TAKEN",
                    "This Google account conflicts with an existing user",
                ) from exc

    # 3) Brand-new user.
    if user is None:
        role = await _student_role(db)
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=None,
            google_id=google_id,
            role_id=role.id,
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            # Concurrent first login (two tabs): the other request won the race.
            await db.rollback()
            user = await _find_by_google_id(db, google_id)
            if user is None:
                user = await _find_by_email(db, email)
            if user is None:
                raise _error(
                    status.HTTP_409_CONFLICT,
                    "EMAIL_TAKEN",
                    "This Google account conflicts with an existing user",
                )
        else:
            is_new_user = True

    user = await get_user_with_role(db, user.id)
    if user is None:
        raise _error(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "User no longer exists",
        )

    role_name = user.role.name if user.role else "student"
    token = create_access_token(user.id, role_name)
    return {"token": token, "user": serialize_user(user), "is_new_user": is_new_user}
