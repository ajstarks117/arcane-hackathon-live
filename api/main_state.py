"""Shared live pipeline telemetry (kept for the legacy /api/status endpoint)."""

def _agents() -> dict:
    return {
        "analyst": "idle",
        "bisect": "idle",
        "patch_generator": "idle",
        "validator": "idle",
        "pr_agent": "idle",
    }


pipeline_status = {
    "current_state": "IDLE",
    "last_event": None,
    "agents": _agents(),
    "pr_url": None,
    "error": None,
    "current_run_id": None,
}


def reset_agents() -> None:
    pipeline_status["agents"] = _agents()
