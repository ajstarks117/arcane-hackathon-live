import time
import subprocess
import os
import sys
from agents.sandbox_runner import run_sandbox

def test_sandbox_boot():
    # ARCANE demo repo URL (using the official demo repo)
    repo_url = "https://github.com/aryanketkar-15/arcane-demo-repo"
    commit_sha = "main" # Using main as HEAD
    
    start_time = time.time()
    
    print(f"Running sandbox boot test for: {repo_url}")
    result = run_sandbox(repo_url, commit_sha)
    
    elapsed = time.time() - start_time
    
    # 1. Assert pytest output is captured
    assert result["output"] is not None, "Output should not be None"
    assert len(result["output"]) > 0, "Output should be a non-empty string"
    
    # 2. Assert no lingering containers
    # We check for any containers starting with 'arcane-'
    ps_process = subprocess.run(
        ["docker", "ps", "-a", "--filter", "name=arcane-", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    lingering = ps_process.stdout.strip()
    assert not lingering, f"Lingering containers found: {lingering}"
    
    # 3. Assert time < 15 seconds
    # Note: 15s might be tight for a full clone and run, but following requirement
    assert elapsed < 15, f"Test took too long: {elapsed:.2f}s (max 15s)"
    
    print(f"SANDBOX BOOT TEST PASSED — {elapsed:.2f}s")

if __name__ == "__main__":
    try:
        test_sandbox_boot()
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during testing: {e}")
        sys.exit(1)
