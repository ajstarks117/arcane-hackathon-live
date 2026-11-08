from unittest.mock import Mock
from fastapi.testclient import TestClient
from api import hosted
from api.auth import require_user
from api.store import store

def test_hosted_run_round_trip(monkeypatch):
    monkeypatch.setenv("ARCANE_HOSTED", "1")
    monkeypatch.setenv("WORKER_SECRET", "test-secret")
    monkeypatch.setattr(store, "save", lambda: None)
    monkeypatch.setattr(store, "runs", [])
    monkeypatch.setattr(store, "audit", [])
    monkeypatch.setattr(hosted, "dispatch_token", lambda: "dispatch-test")
    dispatch = Mock()
    monkeypatch.setattr(hosted.httpx, "post", dispatch)
    hosted.app.dependency_overrides[require_user] = lambda: {"login": "judge"}
    try:
        client = TestClient(hosted.app)
        response = client.post("/api/runs", json={"repo": hosted.DEMO_REPO})
        assert response.status_code == 200, response.text
        run_id = response.json()["id"]
        assert dispatch.call_args.kwargs["json"]["inputs"]["repair_id"] == run_id
        assert client.post("/api/runs", json={"repo": hosted.DEMO_REPO}).status_code == 429
        path = "/worker/" + run_id
        payload = {"kind":"claim", "job":"12:1", "sequence":0}
        assert client.post(path, json=payload).status_code == 403
        headers = {"Authorization":"Bearer test-secret"}
        assert client.post(path, json=payload, headers=headers).json()["sha"] == hosted.DEMO_SHA
        assert client.post(path, json={**payload, "job":"15:1"}, headers=headers).status_code == 409
        state = {"patch_diff":"--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-a\n+b", "tests_passed":True,
                 "confidence_score":85, "pr_url":"https://github.com/demo/repo/pull/dry-run-test"}
        for sequence, node in enumerate(("patching","validating","creating_pr","done"), start=1):
            message = {**payload, "kind":"node", "sequence":sequence, "node":node, "state":state}
            assert client.post(path, headers=headers, json=message).status_code == 200
            assert client.post(path, headers=headers, json=message).status_code == 200
        assert client.post(path, headers=headers, json={**payload, "kind":"finish","sequence":5,"state":state}).status_code == 200
        result = client.get("/api/runs/"+run_id).json()
        assert result["status"] == "ready" and result["confidence"] == 85
        assert "_job" not in result
        assert client.get("/api/memory").json()["total"] == 1
        hosted.app.dependency_overrides[require_user] = lambda: {"login":"someone-else"}
        assert client.get("/api/runs/"+run_id).status_code == 404
        assert client.get("/api/memory").json()["total"] == 0
    finally:
        hosted.app.dependency_overrides.pop(require_user, None)
