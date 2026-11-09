"""Hosted repair uses only the connected owner's credentials and never fabricates validation."""
import base64
import hashlib
import hmac
import json

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import live


def test_failed_push_and_manual_url_share_one_draft_pr(monkeypatch):
    monkeypatch.setenv("WORKER_SECRET", "temporary-test-secret")
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://api.example")
    docs, posts = {}, []
    monkeypatch.setattr(live.cloud_db,"read",lambda k,d: docs.get(k,d))
    monkeypatch.setattr(live.cloud_db,"write",lambda k,v: docs.update({k:v}))
    monkeypatch.setattr(live.store,"runs",[])
    monkeypatch.setattr(live.store,"save",lambda: None)
    monkeypatch.setattr(live,"generate",lambda key,p: {"path":"app.py","cause":"Incorrect result"} if "source" in p and isinstance(p["source"],dict) else {"before":"return 2","after":"return 3"})
    url = "https://github.com/judge/sample/actions/runs/7"
    run = {"id":7,"name":"CI","run_number":4,"event":"push","conclusion":"failure","html_url":url,"head_sha":"abc","head_branch":"main","head_repository":{"full_name":"judge/sample"}}
    fixture = {
        "/user":{"login":"judge"}, "/repos/judge/sample":{"permissions":{"admin":True},"full_name":"judge/sample"},
        "/hooks":[], "/actions/runs/7":run, "/actions/runs/7/jobs":{"jobs":[{"id":2,"name":"pytest","steps":[],"conclusion":"failure"}]},
        "/check-runs/2/annotations":[{"path":"app.py","message":"AssertionError: expected 3"}],
        "/commits/abc":{"files":[{"filename":"app.py","status":"modified"}],"commit":{"tree":{"sha":"root"}}},
        "/contents/app.py":{"type":"file","size":23,"content":base64.b64encode(b"def f():\n    return 2\n").decode()},
        "/branches/main":{"commit":{"sha":"abc"}},"/git/trees/root":{"tree":[{"path":"app.py","mode":"100644"}]}, "/pulls":[]
    }
    def handle(req):
        assert req.headers["authorization"]=="Bearer repo-token"
        endpoint=req.url.path.removeprefix("/repos/judge/sample") or req.url.path
        if req.method=="POST":
            data=json.loads(req.content)
            posts.append((endpoint,data))
            return httpx.Response(201,json={"sha":"xyz","id":1,"html_url":"https://github.com/judge/sample/pull/8"})
        if endpoint not in fixture: return httpx.Response(404)
        return httpx.Response(200,json=fixture[endpoint])
    monkeypatch.setattr(live,"github",lambda tok:httpx.Client(base_url="https://api.github.com",transport=httpx.MockTransport(handle),headers={"Authorization":"Bearer "+tok}))
    app=FastAPI()
    app.include_router(live.router)
    app.dependency_overrides[live.require_user]=lambda:{"login":"judge"}
    client=TestClient(app)
    assert client.put("/api/live/key",json={"key":"gemini-test"}).is_success
    assert client.post("/api/live/connect",json={"repo":"judge/sample","token":"repo-token"}).is_success
    assert "gemini-test" not in str(docs) and "repo-token" not in str(docs)
    body=json.dumps({"repository":{"full_name":"judge/sample"},"action":"completed","workflow_run":run}).encode()
    assert client.post("/api/live/events",content=body).status_code==403
    digest=hmac.new(live.signature("judge/sample").encode(),body,hashlib.sha256).hexdigest()
    assert client.post("/api/live/events",content=body,headers={"x-hub-signature-256":"sha256="+digest}).is_success
    result=client.post("/api/live/runs",json={"url":url}).json()
    assert result["status"]=="ready" and result["testsPassed"] is None and result["prUrl"].endswith("/8"),result
    assert [p for p in posts if p[0]=="/pulls"][0][1]["draft"] is True
    assert sum(p[0]=="/pulls" for p in posts)==1
    app.dependency_overrides[live.require_user]=lambda:{"login":"another-judge"}
    assert client.get("/api/live/settings").json()=={"repo":"","configured":False}
    assert client.post("/api/live/runs",json={"url":url}).status_code==403
