from typing import Annotated, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from jwt import PyJWKClient

from app.config import settings


http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)]):
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    token = creds.credentials

    issuer = f"https://{settings.auth0_domain}/"
    jwks_url = issuer + ".well-known/jwks.json"

    try:
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_audience,
            issuer=issuer,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    return payload  # contains sub (user id), email, etc.

