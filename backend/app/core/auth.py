import httpx
from jose import jwt, JWTError
from pydantic import BaseModel
from app.core.config import get_settings
from app.core.security import generate_state, generate_nonce, generate_pkce_pair

settings = get_settings()


class OIDCConfig(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    userinfo_endpoint: str
    end_session_endpoint: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    id_token: str | None = None
    scope: str


class UserInfo(BaseModel):
    sub: str
    email: str | None = None
    name: str | None = None
    preferred_username: str | None = None
    roles: list[str] = []


_oidc_config: OIDCConfig | None = None


async def get_oidc_config() -> OIDCConfig:
    global _oidc_config
    if _oidc_config:
        return _oidc_config
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.oidc_issuer}/.well-known/openid-configuration"
        )
        resp.raise_for_status()
        data = resp.json()
        _oidc_config = OIDCConfig(
            issuer=data["issuer"],
            authorization_endpoint=data["authorization_endpoint"],
            token_endpoint=data["token_endpoint"],
            jwks_uri=data["jwks_uri"],
            userinfo_endpoint=data["userinfo_endpoint"],
            end_session_endpoint=data.get("end_session_endpoint", ""),
        )
        return _oidc_config


def build_auth_url(
    redirect_uri: str,
    state: str,
    nonce: str,
    code_challenge: str,
    scopes: list[str] | None = None,
) -> str:
    config = _oidc_config or OIDCConfig(
        issuer=settings.oidc_issuer,
        authorization_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/auth",
        token_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/token",
        jwks_uri=f"{settings.oidc_issuer}/protocol/openid-connect/certs",
        userinfo_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/userinfo",
        end_session_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/logout",
    )
    params = {
        "client_id": settings.oidc_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes or ["openid", "profile", "email", "roles"]),
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    from urllib.parse import urlencode
    return f"{config.authorization_endpoint}?{urlencode(params)}"


async def exchange_code_for_tokens(
    code: str,
    redirect_uri: str,
    code_verifier: str,
) -> TokenResponse:
    config = await get_oidc_config()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            config.token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
                "code_verifier": code_verifier,
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return TokenResponse(**resp.json())


async def get_userinfo(access_token: str) -> UserInfo:
    config = await get_oidc_config()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            config.userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        data = resp.json()
        roles = data.get("realm_access", {}).get("roles", [])
        return UserInfo(
            sub=data["sub"],
            email=data.get("email"),
            name=data.get("name"),
            preferred_username=data.get("preferred_username"),
            roles=roles,
        )


async def validate_id_token(id_token: str, nonce: str) -> dict:
    config = await get_oidc_config()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(config.jwks_uri)
        resp.raise_for_status()
        jwks = resp.json()

    unverified_header = jwt.get_unverified_header(id_token)
    kid = unverified_header.get("kid")
    if not kid:
        raise JWTError("Missing kid in token header")

    key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
    if not key:
        raise JWTError("Key not found in JWKS")

    from jose.utils import base64url_decode
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    n = base64url_decode(key["n"].encode()).hex()
    e = base64url_decode(key["e"].encode()).hex()
    public_key = rsa.RSAPublicNumbers(
        int(e, 16), int(n, 16)
    ).public_key()

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    payload = jwt.decode(
        id_token,
        pem,
        algorithms=["RS256"],
        audience=settings.oidc_client_id,
        issuer=config.issuer,
        options={"verify_nonce": False},
    )

    if payload.get("nonce") != nonce:
        raise JWTError("Invalid nonce")

    return payload


def build_logout_url(redirect_uri: str, id_token_hint: str | None = None) -> str:
    config = _oidc_config or OIDCConfig(
        issuer=settings.oidc_issuer,
        authorization_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/auth",
        token_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/token",
        jwks_uri=f"{settings.oidc_issuer}/protocol/openid-connect/certs",
        userinfo_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/userinfo",
        end_session_endpoint=f"{settings.oidc_issuer}/protocol/openid-connect/logout",
    )
    from urllib.parse import urlencode
    params = {"post_logout_redirect_uri": redirect_uri}
    if id_token_hint:
        params["id_token_hint"] = id_token_hint
    return f"{config.end_session_endpoint}?{urlencode(params)}"