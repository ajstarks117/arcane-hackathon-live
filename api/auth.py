"""GitHub OAuth login, per-user sessions and repository access."""
import json
import logging
import os
import secrets
import threading
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.store import DATA_DIR, default_repo, now_iso, store

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/api")

SESSION_FILE = os.path.join(DATA_DIR, "sessions.json")
COOKIE = "arcane_session"
SCOPES = "read:user"
_lock = threading.Lock()
_states: set[str] = set()


def oauth_configured() -> bool:
    return bool(os.getenv("GITHUB_CLIENT_ID") and os.getenv("GITHUB_CLIENT_SECRET"))


def app_url() -> str:
    return os.getenv("APP_URL", "http://localhost:5173").rstrip("/")


def _load() -> dict:
    if os.getenv("DATABASE_URL"):
        from api.cloud_db import read
        return read("sessions", {})
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(sessions: dict) -> None:
    if os.getenv("DATABASE_URL"):
        from api.cloud_db import write
        write("sessions", sessions)
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = SESSION_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sessions, f)
    os.replace(tmp, SESSION_FILE)
    try:
        os.chmod(SESSION_FILE, 0o600)
    except Exception:
        pass


def current_user(request: Request) -> Optional[dict]:
    """Returns the signed-in user (incl. token) or None."""
    sid = request.cookies.get(COOKIE)
    if not sid:
        return None
    with _lock:
        return _load().get(sid)


def require_user(request: Request) -> Optional[dict]:
    """Dependency: 401 when OAuth is enabled and nobody is signed in."""
    user = current_user(request)
    if user is None and oauth_configured():
        raise HTTPException(401, "Sign in with GitHub to continue.")
    return user


def public_user(user: Optional[dict]) -> Optional[dict]:
    if not user:
        return None
    return {k: user.get(k) for k in ("login", "name", "email", "avatar")}


def token_for_login(login: str) -> Optional[str]:
    with _lock:
        for u in _load().values():
            if u.get("login") == login:
                return u.get("token")
    return None


def token_for_repo(repo: str) -> Optional[str]:
    """Token of the user who watches `repo` (used for webhook-triggered runs)."""
    login = store.watched.get(repo)
    if login:
        tok = token_for_login(login)
        if tok:
            return tok
    owner = repo.split("/")[0] if "/" in repo else repo
    tok = token_for_login(owner)
    if tok:
        return tok
    with _lock:
        sessions = _load()
        for u in sessions.values():
            if u.get("token"):
                return u.get("token")
    return None


# ── OAuth flow ───────────────────────────────────────────────────────────────

@auth_router.get("/auth/config")
def auth_config():
    return {"oauth": oauth_configured()}


@auth_router.get("/auth/github/login")
def login():
    if not oauth_configured():
        raise HTTPException(503, "GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET are not set in .env")
    state = secrets.token_urlsafe(24)
    q = urlencode(
        {
            "client_id": os.environ["GITHUB_CLIENT_ID"],
            "redirect_uri": f"{app_url()}/api/auth/github/callback",
            "scope": SCOPES,
            "state": state,
        }
    )
    resp = RedirectResponse(f"https://github.com/login/oauth/authorize?{q}")
    resp.set_cookie("arcane_oauth_state", state, httponly=True, secure=True, samesite="lax", max_age=600)
    return resp


@auth_router.get("/auth/github/callback")
def callback(request: Request, code: str = "", state: str = "", error: str = ""):
    if error:
        return RedirectResponse(f"{app_url()}/?auth_error={error}")
    if not state or not secrets.compare_digest(request.cookies.get("arcane_oauth_state", ""), state):
        return RedirectResponse(f"{app_url()}/?auth_error=invalid_state")
    _states.discard(state)
    try:
        tok = httpx.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": os.environ["GITHUB_CLIENT_ID"],
                "client_secret": os.environ["GITHUB_CLIENT_SECRET"],
                "code": code,
                "redirect_uri": f"{app_url()}/api/auth/github/callback",
            },
            headers={"Accept": "application/json"},
            timeout=15,
        ).json()
        token = tok.get("access_token")
        if not token:
            logger.warning(f"[Auth] token exchange failed: {tok.get('error')}")
            return RedirectResponse(f"{app_url()}/?auth_error={tok.get('error', 'token_exchange_failed')}")
        gh = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=15,
        ).json()
    except Exception as e:
        logger.error(f"[Auth] OAuth error: {e}")
        return RedirectResponse(f"{app_url()}/?auth_error=network")
    if not gh.get("login"):
        raise HTTPException(401, "GitHub identity verification failed")
    sid = secrets.token_urlsafe(32)
    with _lock:
        sessions = _load()
        sessions[sid] = {
            "login": gh.get("login"),
            "name": gh.get("name") or gh.get("login"),
            "email": gh.get("email") or "",
            "avatar": gh.get("avatar_url") or "",
            "token": "",
            "createdAt": now_iso(),
        }
        _save(sessions)
    store.add_audit("Signed in with GitHub", "Workspace", gh.get("login", "unknown"))
    resp = RedirectResponse(f"{app_url()}/")
    resp.set_cookie(COOKIE, sid, httponly=True, secure=app_url().startswith("https://"), samesite="lax", max_age=60 * 60 * 24 * 14, path="/")
    return resp


@auth_router.get("/me")
def me(request: Request):
    user = current_user(request)
    if user is None and oauth_configured():
        raise HTTPException(401, "Not signed in")
    pub = public_user(user) or {"login": "local", "name": "Local user", "email": "", "avatar": ""}
    pub["workspace"] = store.settings.get("workspace", "Team Bahadur")
    pub["oauth"] = oauth_configured()
    return pub


@auth_router.post("/auth/logout")
def logout(request: Request, response: Response):
    sid = request.cookies.get(COOKIE)
    if sid:
        with _lock:
            s = _load()
            s.pop(sid, None)
            _save(s)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


# ── repositories ─────────────────────────────────────────────────────────────

@auth_router.get("/github/repos")
def my_repos(user=Depends(require_user)):
    token = (user or {}).get("token") or os.getenv("GITHUB_PAT")
    if not token:
        raise HTTPException(400, "No GitHub token available.")
    try:
        r = httpx.get(
            "https://api.github.com/user/repos",
            params={"per_page": 100, "sort": "pushed", "affiliation": "owner,collaborator,organization_member"},
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=20,
        )
        if r.status_code == 401:
            raise HTTPException(401, "GitHub rejected the token — sign in again.")
        r.raise_for_status()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"GitHub request failed: {e}")
    return {
        "repos": [
            {
                "name": x["full_name"],
                "private": x["private"],
                "defaultBranch": x["default_branch"],
                "pushedAt": x["pushed_at"],
                "watched": x["full_name"] in store.watched,
                "canAdmin": bool((x.get("permissions") or {}).get("admin")),
            }
            for x in r.json()
        ]
    }


class WatchBody(BaseModel):
    repo: str
    webhook: bool = True


@auth_router.post("/github/watch")
def watch_repo(body: WatchBody, user=Depends(require_user)):
    login_name = (user or {}).get("login", "local")
    token = (user or {}).get("token") or os.getenv("GITHUB_PAT")
    if "/" not in body.repo:
        raise HTTPException(400, "Repository must look like owner/name.")
    hook_msg = "Webhook not created."
    if body.webhook:
        public = os.getenv("PUBLIC_URL", "").rstrip("/")
        secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if not public:
            hook_msg = "Watching, but no webhook yet: set PUBLIC_URL in .env (your tunnel URL) to create it automatically."
        elif not (token and secret):
            hook_msg = "Watching, but the webhook needs a token and GITHUB_WEBHOOK_SECRET."
        else:
            try:
                r = httpx.post(
                    f"https://api.github.com/repos/{body.repo}/hooks",
                    json={
                        "name": "web",
                        "active": True,
                        "events": ["push"],
                        "config": {"url": f"{public}/webhook", "content_type": "json", "secret": secret},
                    },
                    headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                    timeout=20,
                )
                if r.status_code in (200, 201):
                    hook_msg = "Webhook created."
                elif r.status_code == 422:
                    hook_msg = "Webhook already exists."
                else:
                    hook_msg = f"GitHub refused the webhook ({r.status_code}): you need admin rights on the repo."
            except Exception as e:
                hook_msg = f"Webhook request failed: {e}"
    store.watched[body.repo] = login_name
    names = [r["name"] for r in store.settings.get("repositories", [])]
    if body.repo not in names:
        store.settings.setdefault("repositories", []).append(default_repo(body.repo))
    store.add_audit("Started watching a repository", body.repo, login_name)
    store.save()
    return {"ok": True, "message": hook_msg}


@auth_router.delete("/github/watch")
def unwatch_repo(repo: str, user=Depends(require_user)):
    store.watched.pop(repo, None)
    store.settings["repositories"] = [r for r in store.settings.get("repositories", []) if r["name"] != repo]
    store.add_audit("Stopped watching a repository", repo, (user or {}).get("login", "local"))
    store.save()
    return {"ok": True}
