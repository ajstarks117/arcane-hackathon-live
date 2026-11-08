import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables before other imports
load_dotenv(override=True)

import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.webhook import router as webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: check env vars on reload
for k, v in os.environ.items():
    if k.startswith("GITHUB_"):
        logger.info(f"[Debug] Env: {k} = {'*' * len(v)}")

from agents.orchestrator import graph

from api.main_state import pipeline_status, reset_agents
from api.recorder import apply_node, finish_run, run_log_handler, start_run
from api.auth import auth_router, token_for_login, token_for_repo
from api.routes import router as api_router, github_token
from api.store import store

# ── Async consumer: drains the webhook queue → runs LangGraph ────────────────

AGENT_FOR_NODE = {
    "analyzing": ("analyst", "bisect", "BISECTING"),
    "bisecting": ("bisect", "patch_generator", "PATCHING"),
    "patching": ("patch_generator", "validator", "VALIDATING"),
    "validating": ("validator", "pr_agent", "GENERATING TEST"),
}


async def process_events(event_queue: asyncio.Queue):
    """Pulls events off the queue and streams each through the LangGraph workflow,
    recording every step into the run store so the dashboard is live."""
    logger.info("[Consumer] Event processor started — waiting for events")
    logging.getLogger().addHandler(run_log_handler)
    while True:
        event = await event_queue.get()
        run = store.get_run(event.get("run_id", "")) or store.create_run(event)
        logger.info(f"[Consumer] Processing {event.get('repo_full_name')} ({str(event.get('commit_sha', '?'))[:7]})")

        reset_agents()
        pipeline_status.update(
            pr_url=None, error=None, current_run_id=run["id"], current_state="ANALYZING",
            last_event={
                "repo": event.get("repo_full_name"),
                "sha": event.get("commit_sha"),
                "triggered_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        pipeline_status["agents"]["analyst"] = "running"
        run_log_handler.run = run
        start_run(run)

        final = {}
        error = None
        token_ctx = None
        try:
            initial_state = {
                "event": event,
                "repo_full_name": event.get("repo_full_name", ""),
                "commit_sha": event.get("commit_sha", ""),
                "failure_log": event.get("failure_log", ""),
                "failing_test": "unknown_test",
                "retry_count": 0,
            }
            tok = token_for_login(run.get("owner", "")) or token_for_repo(run["repo"])
            token_ctx = github_token(tok)
            token_ctx.__enter__()
            async for step in graph.astream(initial_state):
                for node_name, state in step.items():
                    final = state
                    logger.info(f"[Consumer] 🔄 Node completed: {node_name}")
                    apply_node(run, node_name, state)
                    if node_name in AGENT_FOR_NODE:
                        done, nxt, label = AGENT_FOR_NODE[node_name]
                        pipeline_status["agents"][done] = "done"
                        pipeline_status["agents"][nxt] = "running"
                        pipeline_status["current_state"] = label
                    elif node_name == "generating_test":
                        pipeline_status["current_state"] = "CREATING PR"
                    elif node_name == "creating_pr":
                        pipeline_status["agents"]["pr_agent"] = "done"
                    elif node_name == "done":
                        pipeline_status["current_state"] = "DONE"
                    elif node_name == "escalated":
                        pipeline_status["current_state"] = "ESCALATED"
                        pipeline_status["error"] = final.get("error")
        except Exception as e:
            error = str(e)
            logger.error(f"[Consumer] Unhandled error: {error}")
            if "422" in error and "pull request already exists" in error.lower():
                error = None
        finally:
            if token_ctx is not None:
                token_ctx.__exit__(None, None, None)
            run_log_handler.run = None
            try:
                finish_run(run, final, error)
            except Exception as e:  # never let bookkeeping kill the consumer
                logger.error(f"[Consumer] finish_run failed: {e}")
            pipeline_status["pr_url"] = run.get("prUrl")
            pipeline_status["current_state"] = {"ready": "DONE", "working": "DONE"}.get(run["status"], "ESCALATED")
            pipeline_status["error"] = run.get("error")
            event_queue.task_done()


# ── App lifecycle ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background consumer on startup, cancel on shutdown."""
    # Create the queue inside the running event loop
    app.state.event_queue = asyncio.Queue(maxsize=10)
    
    task = asyncio.create_task(process_events(app.state.event_queue))
    logger.info("[Lifespan] Background event processor launched")
    yield
    task.cancel()
    logger.info("[Lifespan] Background event processor cancelled")


app = FastAPI(title="ARCANE API", lifespan=lifespan)

# ── CORS — allow the React dev server (port 5173) to talk to FastAPI ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8443", "http://127.0.0.1:8443"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(auth_router)
app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/status")
async def get_status():
    """Returns the current LangGraph pipeline telemetry for the dashboard."""
    return pipeline_status

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
