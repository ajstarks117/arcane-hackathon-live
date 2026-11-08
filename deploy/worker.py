import asyncio
import os
import time
import httpx

job = os.environ["GITHUB_RUN_ID"] + ":" + os.environ["GITHUB_RUN_ATTEMPT"]
url = os.environ["ARCANE_API_URL"].rstrip("/") + "/worker/" + os.environ["REPAIR_ID"]

def post(kind, sequence, **fields):
    for attempt in range(5):
        try:
            response = httpx.post(url, headers={"Authorization": "Bearer " + os.environ["WORKER_SECRET"]},
                json={"job": job, "kind": kind, "sequence": sequence, **fields}, timeout=60)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500 or attempt == 4:
                raise
        except httpx.TransportError:
            if attempt == 4:
                raise
        time.sleep(2 ** attempt)

async def main():
    payload = post("claim", 0)
    from agents.chroma_memory import init_memory, store_patch
    from agents.orchestrator import graph
    client = init_memory(os.environ["CHROMADB_PATH"])
    for item in payload["memory"]:
        store_patch(client, item["failureLog"], item["rootCause"], item["patchDiff"], item["failingTest"], item["sha"])
    event = {"repo_full_name": payload["repo"], "commit_sha": payload["sha"], "failure_log": payload["log"], "branch": "main"}
    state = {**event, "event": event, "retry_count": 0, "failing_test": "unknown_test"}
    sequence = 0
    async for step in graph.astream(state):
        for node, changes in step.items():
            state.update(changes)
            sequence += 1
            keys = ("agents_used","failing_test","failing_file","failing_line","suspected_function","root_cause_summary","fast_forward_patch","patch_diff","bisect_intent_report","cascade_report","conflict_detected","conflict_action","conflict_details","tests_passed","confidence_score","auto_approved","validator_summary","regression_test_code","pr_url","retry_count","error")
            public = {k: state[k] for k in keys if k in state}
            post("node", sequence, node=node, state=public)
    post("finish", sequence + 1, state=public)

if __name__ == "__main__":
    asyncio.run(main())
