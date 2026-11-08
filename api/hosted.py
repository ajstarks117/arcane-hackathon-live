"""Web process on Render. GitHub Actions executes the graph on an ephemeral Docker host."""
import asyncio
import os
import secrets
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from api.github_app import router as setup_router, configure_oauth, credentials, dispatch_token
from api.auth import auth_router
from api.routes import router
from api.recorder import start_run, apply_node, finish_run
from api.store import store

lock = threading.RLock()
DEMO_REPO = "ajstarks117/TEST-REPO"
DEMO_SHA = "1e690ab160af391f1223dc0ca46bb75db0cd316a"
DEMO_LOG = "FAILED tests/test_auth.py::test_valid_token - ValueError: Token must be at least 10 characters long. src/auth.py validate_token rejects a valid 20-character token."

def expire():
    now = datetime.now(timezone.utc)
    for run in store.runs:
        if run["status"] == "working" and (now - datetime.fromisoformat(run["queuedAt"])).total_seconds() > 3600:
            finish_run(run, {}, "The hosted worker did not finish within one hour. Retry the repair.")

def dispatch(event):
    with lock:
        expire()
        if event["repo_full_name"] != DEMO_REPO or event["commit_sha"] != DEMO_SHA:
            raise HTTPException(400, "Use the pinned public token-validation build for this deployment.")
        if any(r["status"] == "working" for r in store.runs):
            raise HTTPException(429, "A repair is already running. Try again after it finishes.")
        run = store.create_run(event)
        store.log(run, "INFO", "Dispatching GitHub Actions worker")
        store.save()
        try:
            response = httpx.post("https://api.github.com/repos/ajstarks117/arcane-hackathon-live/actions/workflows/repair.yml/dispatches",
                headers={"Authorization": "Bearer " + dispatch_token()},
                json={"ref": "main", "inputs": {"repair_id": run["id"]}}, timeout=15)
            response.raise_for_status()
        except Exception:
            finish_run(run, {}, "GitHub did not confirm workflow dispatch. Check Actions access and retry.")
            raise HTTPException(502, run["error"])
        store.add_audit("Queued repair", run["repo"], event.get("owner", "ARCANE"))
        return run

@asynccontextmanager
async def lifespan(app):
    for key in ("APP_URL", "WORKER_SECRET", "DATABASE_URL"):
        if not os.getenv(key):
            raise RuntimeError(f"Missing hosted setting {key}")
    configure_oauth(credentials())
    async def monitor():
        while True:
            with lock:
                expire()
            await asyncio.sleep(60)
    task = asyncio.create_task(monitor())
    try:
        yield
    finally:
        task.cancel()

app = FastAPI(lifespan=lifespan)
app.include_router(setup_router)
app.include_router(auth_router)
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}

def authenticate(authorization: str = Header(default="")):
    if not secrets.compare_digest(authorization, "Bearer " + os.environ["WORKER_SECRET"]):
        raise HTTPException(403)

class Update(BaseModel):
    job: str = Field(pattern=r"^[0-9]+:[0-9]+$")
    sequence: int = Field(ge=0)
    kind: str = Field(pattern="^(claim|node|finish|error)$")
    node: str = ""
    state: dict = Field(default_factory=dict)
    error: str = ""

def memories(owner):
    return [r for r in store.runs if r["owner"] == owner and r["status"] == "ready" and r["testsPassed"] and r["patchDiff"] and not r["memoryHit"]]

@app.post("/worker/{repair_id}", dependencies=[Depends(authenticate)])
def update(repair_id: str, message: Update):
    with lock:
        r = store.get_run(repair_id)
        if not r:
            raise HTTPException(404)
        if r.get("_job", message.job) != message.job:
            raise HTTPException(409, "This repair belongs to another job.")
        if message.kind == "claim" and r["status"] == "working":
            if "_job" not in r:
                r["_job"] = message.job
                r["_sequence"] = 0
                start_run(r)
            history = [m for m in memories(r["owner"]) if store.memory_flags.get(m["id"], True)]
            return {"repo": r["repo"], "sha": r["sha"], "log": r["failureLog"],
                    "memory": [{k: m[k] for k in ("failureLog","rootCause","patchDiff","failingTest","sha")} for m in history[:1]]}
        if message.sequence <= r.get("_sequence", -1):
            return {"ok": True}
        if r["status"] != "working" or (message.kind != "error" and "_job" not in r):
            raise HTTPException(409)
        r["_sequence"] = message.sequence
        if message.kind == "node":
            store.log(r, "INFO", "Completed " + message.node)
            apply_node(r, message.node, message.state)
        elif message.kind == "error":
            finish_run(r, {}, message.error[:1000] or "GitHub Actions worker failed")
        elif message.kind == "finish":
            finish_run(r, message.state)
        store.save()
        return {"ok": True}


@app.post("/worker-smoke", dependencies=[Depends(authenticate)])
def smoke(manual_dispatch: bool = False):
    event = {"repo_full_name": DEMO_REPO, "commit_sha": DEMO_SHA, "failure_log": DEMO_LOG,
             "branch": "main", "source": "deployment-check", "owner": "deployment-check"}
    if manual_dispatch:
        # Let the deployment operator test the worker before enabling user sign-in.
        with lock:
            expire()
            if any(r["status"] == "working" for r in store.runs):
                raise HTTPException(429, "A repair is already running.")
            run = store.create_run(event)
    else:
        run = dispatch(event)
    return {"id": run["id"]}

@app.get("/worker-smoke/{repair_id}", dependencies=[Depends(authenticate)])
def smoke_result(repair_id: str):
    run = store.get_run(repair_id)
    if not run or run["owner"] != "deployment-check":
        raise HTTPException(404)
    return {k:run[k] for k in ("status","stage","testsPassed","confidence","patchDiff","reason","validatorSummary")}
