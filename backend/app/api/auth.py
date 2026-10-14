from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.core.config import get_settings
from app.core.database import get_db
from app.core.auth import (
    get_oidc_config,
    build_auth_url,
    exchange_code_for_tokens,
    get_userinfo,
    validate_id_token,
    build_logout_url,
)
from app.core.security import generate_state, generate_nonce, generate_pkce_pair, encrypt_token, decrypt_token
from app.models import User
from app.schemas import (
    AuthURLResponse,
    CallbackRequest,
    TokenResponse,
    UserRead,
    ErrorResponse,
)

router = APIRouter()
settings = get_settings()


@router.get("/login", response_model=AuthURLResponse)
async def login(redirect_uri: str | None = None):
    state = generate_state()
    nonce = generate_nonce()
    code_verifier, code_challenge = generate_pkce_pair()

    auth_url = build_auth_url(
        redirect_uri=redirect_uri or settings.oidc_redirect_uri,
        state=state,
        nonce=nonce,
        code_challenge=code_challenge,
    )

    return AuthURLResponse(
        auth_url=auth_url,
        state=state,
        nonce=nonce,
        code_verifier=code_verifier,
    )


@router.post("/callback", response_model=TokenResponse)
async def callback(
    request: CallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    token_resp = await exchange_code_for_tokens(
        code=request.code,
        redirect_uri=settings.oidc_redirect_uri,
        code_verifier=request.code_verifier,
    )

    await validate_id_token(token_resp.id_token, request.nonce)

    userinfo = await get_userinfo(token_resp.access_token)

    result = await db.execute(select(User).where(User.sub == userinfo.sub))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            sub=userinfo.sub,
            email=userinfo.email,
            name=userinfo.name,
            preferred_username=userinfo.preferred_username,
            roles=json.dumps(userinfo.roles),
        )
        db.add(user)
    else:
        user.email = userinfo.email
        user.name = userinfo.name
        user.preferred_username = userinfo.preferred_username
        user.roles = json.dumps(userinfo.roles)

    await db.commit()
    await db.refresh(user)

    encrypted_access = encrypt_token(token_resp.access_token)
    encrypted_refresh = encrypt_token(token_resp.refresh_token) if token_resp.refresh_token else None

    response.set_cookie(
        key="access_token",
        value=encrypted_access,
        httponly=True,
        secure=not settings.demo_mode,
        samesite="lax",
        max_age=token_resp.expires_in,
        path="/",
    )
    if encrypted_refresh:
        response.set_cookie(
            key="refresh_token",
            value=encrypted_refresh,
            httponly=True,
            secure=not settings.demo_mode,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
        )

    return TokenResponse(
        access_token=token_resp.access_token,
        token_type=token_resp.token_type,
        expires_in=token_resp.expires_in,
        refresh_token=token_resp.refresh_token,
    )


@router.post("/logout")
async def logout(response: Response, id_token_hint: str | None = None):
    logout_url = build_logout_url(
        redirect_uri=settings.oidc_redirect_uri.replace("/callback", ""),
        id_token_hint=id_token_hint,
    )
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"logout_url": logout_url}


@router.get("/me", response_model=UserRead)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    access_token_cookie = request.cookies.get("access_token")
    if not access_token_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        access_token = decrypt_token(access_token_cookie)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    userinfo = await get_userinfo(access_token)

    result = await db.execute(select(User).where(User.sub == userinfo.sub))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    import json
    return UserRead(
        id=user.id,
        sub=user.sub,
        email=user.email,
        name=user.name,
        preferred_username=user.preferred_username,
        roles=json.loads(user.roles),
        created_at=user.created_at,
    )