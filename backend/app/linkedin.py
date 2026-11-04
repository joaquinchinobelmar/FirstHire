"""Sign In with LinkedIn using OpenID Connect.

Docs: https://learn.microsoft.com/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2
Setup: create an app at https://www.linkedin.com/developers/apps, add the product
"Sign In with LinkedIn using OpenID Connect", and register the redirect URL
(default http://localhost:5173/api/auth/linkedin/callback).

Scopes: openid profile email. LinkedIn only shares name, email and photo through this
product. Work history and skills are not available to third-party apps, so graduates still
build their Passport from their CV. We store name + email and deliberately discard the
photo, which keeps the blind-review promise.
"""

import base64
import json
import urllib.parse
import urllib.request

from .config import settings

AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = "openid profile email"


class LinkedInError(Exception):
    pass


def authorize_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "state": state,
        "scope": SCOPES,
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def _exchange_code(code: str) -> str:
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.linkedin_redirect_uri,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token = json.loads(resp.read().decode()).get("access_token")
    except Exception as e:
        raise LinkedInError("LinkedIn rejected the sign-in code") from e
    if not token:
        raise LinkedInError("LinkedIn did not return an access token")
    return token


def _userinfo(access_token: str) -> dict:
    req = urllib.request.Request(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        raise LinkedInError("Couldn't read your LinkedIn profile") from e


def profile_from_code(code: str) -> dict:
    """Returns {sub, name, email, email_verified}."""
    if settings.linkedin_mode == "demo":
        if not code.startswith("demo."):
            raise LinkedInError("LinkedIn is not configured on this server")
        try:
            raw = json.loads(base64.urlsafe_b64decode(code[5:] + "==").decode())
        except Exception as e:
            raise LinkedInError("Invalid demo sign-in") from e
        email = str(raw.get("email", "")).strip().lower()
        name = str(raw.get("name", "")).strip()[:120]
        if "@" not in email or not name:
            raise LinkedInError("Name and email are required")
        return {"sub": f"demo-{email}", "name": name, "email": email, "email_verified": True}

    info = _userinfo(_exchange_code(code))
    email = (info.get("email") or "").strip().lower()
    if not info.get("sub") or not email:
        raise LinkedInError("Your LinkedIn account didn't share an email address")
    name = info.get("name") or " ".join(filter(None, [info.get("given_name"), info.get("family_name")])) or email.split("@")[0]
    return {"sub": info["sub"], "name": name[:120], "email": email, "email_verified": bool(info.get("email_verified"))}
