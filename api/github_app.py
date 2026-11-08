"""One-time GitHub App registration and installation-scoped Actions dispatch."""
import html
import json
import os
import secrets

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from github import Auth, GithubIntegration
import httpx

from api import cloud_db

router = APIRouter(prefix="/api/setup/github")
OWNER = "ajstarks117"
REPO = "arcane-hackathon-live"

def credentials():
    return cloud_db.read("github-app", {})

def configure_oauth(config):
    if config:
        os.environ["GITHUB_CLIENT_ID"] = config["client_id"]
        os.environ["GITHUB_CLIENT_SECRET"] = config["client_secret"]

def dispatch_token():
    if os.getenv("ACTIONS_DISPATCH_TOKEN"):
        return os.environ["ACTIONS_DISPATCH_TOKEN"]
    app = credentials()
    if not app:
        raise HTTPException(503, "GitHub App setup is incomplete.")
    integration = GithubIntegration(auth=Auth.AppAuth(app["id"], app["pem"]))
    installation = integration.get_repo_installation(OWNER, REPO)
    return integration.get_access_token(installation.id, permissions={"actions":"write"}).token

@router.get("", response_class=HTMLResponse)
def setup():
    config = credentials()
    if config:
        return RedirectResponse(config["html_url"] + "/installations/new")
    site = os.environ["APP_URL"].rstrip("/")
    manifest = {"name": "ARCANE Repair " + OWNER, "url": site, "public": False,
        "redirect_url": site + "/api/setup/github/complete",
        "callback_urls": [site + "/api/auth/github/callback"],
        "hook_attributes": {"active": False}, "default_permissions": {"actions":"write"}}
    nonce = secrets.token_urlsafe(32)
    response = HTMLResponse('<meta name="viewport" content="width=device-width"><title>Connect ARCANE</title><main style="max-width:42rem;margin:12vh auto;font:18px system-ui"><h1>Connect GitHub to ARCANE</h1><p>Create the deployment app as ajstarks117, then install it on the arcane-hackathon-live repository.</p><form method="post" action="https://github.com/settings/apps/new?state=' + nonce + '"><input type="hidden" name="manifest" value="' + html.escape(json.dumps(manifest), quote=True) + '"><button style="padding:12px">Continue to GitHub</button></form></main>')
    response.set_cookie("arcane_setup", nonce, secure=True, httponly=True, samesite="lax", max_age=600)
    return response

from fastapi import Request
@router.get("/complete")
def complete(request: Request, code: str, state: str):
    if not state or not secrets.compare_digest(request.cookies.get("arcane_setup",""), state):
        raise HTTPException(403, "Setup confirmation expired.")
    if credentials():
        raise HTTPException(409, "App already configured.")
    res = httpx.post("https://api.github.com/app-manifests/" + code + "/conversions", timeout=15)
    res.raise_for_status()
    app = res.json()
    if app.get("owner",{}).get("login","").lower() != OWNER:
        raise HTTPException(403, "Only the repository owner can register this app.")
    config = {k:app[k] for k in ("id","pem","client_id","client_secret","html_url")}
    cloud_db.write("github-app", config)
    configure_oauth(config)
    return RedirectResponse(app["html_url"] + "/installations/new")
