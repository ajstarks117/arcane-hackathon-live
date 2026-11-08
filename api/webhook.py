import os
import hmac
import hashlib
import asyncio
import logging
from fastapi import APIRouter, Request, HTTPException
from api.store import store

router = APIRouter()
logger = logging.getLogger(__name__)

# Branches ARCANE is allowed to watch — ignore all others to prevent loops
WATCHED_BRANCHES = {"main", "master"}

@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Single POST endpoint to receive GitHub Actions CI failure payloads.
    Validates HMAC signature and pushes parsed failure logs into the event queue.
    """
    # 1. Validate X-Hub-Signature-256 header using HMAC-SHA256
    secret_token = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret_token:
        logger.error("GITHUB_WEBHOOK_SECRET environment variable is not set")
        raise HTTPException(status_code=500, detail="Server webhook secret not configured")

    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing X-Hub-Signature-256 header")

    body = await request.body()

    # Calculate expected HMAC
    mac = hmac.new(secret_token.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected_signature = f"sha256={mac.hexdigest()}"

    # Securely compare signatures
    if not hmac.compare_digest(expected_signature, signature_header):
        logger.warning(
            f"Signature mismatch! GitHub sent: {signature_header}, "
            f"Server expected: {expected_signature}."
        )
        raise HTTPException(status_code=403, detail="Invalid signature")

    # 2. Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = request.headers.get("X-Github-Event", "unknown")
    repo = payload.get("repository", {})
    repo_full_name = repo.get("full_name", "")

    # ── LOOP-PREVENTION FILTERS ──────────────────────────────────────────────
    # Filter 1: Only process push events
    if event_type != "push":
        logger.info(f"[Webhook] Ignoring non-push event: {event_type}")
        return {"status": "ignored", "reason": f"event_type={event_type}"}

    # Filter 2: Block pushes to ARCANE's own fix branches (arcane/fix-*)
    ref = payload.get("ref", "")  # e.g. "refs/heads/arcane/fix-abc1234"
    branch = ref.replace("refs/heads/", "")
    if branch.startswith("arcane/") or branch.startswith("arcane-"):
        logger.info(f"[Webhook] Ignoring ARCANE bot branch push: {branch}")
        return {"status": "ignored", "reason": f"bot branch={branch}"}

    # Filter 3: Only watch main/master — ignore feature branches etc.
    if branch not in WATCHED_BRANCHES:
        logger.info(f"[Webhook] Ignoring push to non-watched branch: {branch}")
        return {"status": "ignored", "reason": f"branch={branch} not watched"}

    # Filter 4: Ignore bot/merge commits authored by GitHub Actions or ARCANE
    pusher_name = payload.get("pusher", {}).get("name", "")
    if "arcane" in pusher_name.lower() or "github-actions" in pusher_name.lower():
        logger.info(f"[Webhook] Ignoring push from bot account: {pusher_name}")
        return {"status": "ignored", "reason": f"bot pusher={pusher_name}"}

    # 3. Extract fields
    head_commit = payload.get("head_commit", {})
    commit_sha = head_commit.get("id") or payload.get("check_run", {}).get("head_sha")

    # Failure log: commit message for push events
    check_run = payload.get("check_run", {})
    failure_log = (
        check_run.get("output", {}).get("text")
        or head_commit.get("message")
        or "No failure log provided"
    )

    logger.info(
        f"[Webhook] ✅ Accepted push event: {event_type} for {repo_full_name} "
        f"branch={branch} sha={str(commit_sha)[:7]}"
    )

    # 4. Push event dict to asyncio queue
    event_dict = {
        "repo_full_name": repo_full_name,
        "commit_sha": commit_sha,
        "failure_log": failure_log,
        "branch": branch,
        "commit_message": head_commit.get("message", ""),
        "author": (head_commit.get("author") or {}).get("name", ""),
        "source": "webhook",
        "owner": store.watched.get(repo_full_name, "") or (repo_full_name.split("/")[0] if "/" in repo_full_name else ""),
    }

    # 5. Log dropped events if the queue is full
    try:
        from api.routes import enqueue_event
        enqueue_event(request, event_dict)
        logger.info(f"[Webhook] Queued event: {repo_full_name} ({commit_sha})")
    except (asyncio.QueueFull, HTTPException):
        logger.warning(f"[Webhook] Queue is full. Dropped event for {repo_full_name} ({commit_sha})")

    return {"status": "received"}
