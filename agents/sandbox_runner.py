import subprocess
import os
import uuid
import time
import threading
from typing import Optional, Dict, Any

def warm_sandbox(repo_url: str):
    """
    Starts a background container and pre-clones the repo to save time on the next run.
    """
    # Health check: remove if it exists (even if stopped)
    subprocess.run(["docker", "rm", "-f", "arcane-warm"], capture_output=True)
    
    # Boot warm container
    boot_res = subprocess.run(
        ["docker", "run", "-d", "--name", "arcane-warm", "arcane-sandbox", "sleep", "infinity"],
        capture_output=True
    )
    if boot_res.returncode == 0:
        # Pre-clone the repo
        subprocess.run(["docker", "exec", "-i", "arcane-warm", "git", "clone", repo_url, "."], capture_output=True)

def run_sandbox(repo_url: str, commit_sha: str, patch_diff: Optional[str] = None, extra_test_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Boots a Docker container, clones a repository inside it, applies an optional patch, and runs pytest.
    """
    container_name = f"arcane-{uuid.uuid4().hex[:8]}"
    print(f"Starting container: {container_name}")
    
    t_start = time.perf_counter()
    
    try:
        # Helper to run commands inside the container
        def exec_in_container(cmd, input_str=None, timeout=None):
            return subprocess.run(
                ["docker", "exec", "-i", container_name] + cmd,
                input=input_str,
                capture_output=True,
                text=True,
                timeout=timeout
            )

        # 1. Boot or take warm container
        rename_res = subprocess.run(["docker", "rename", "arcane-warm", container_name], capture_output=True)
        if rename_res.returncode == 0:
            t_boot = time.perf_counter()
            print(f"SANDBOX: container ready in {t_boot - t_start:.2f}s (warmed)")
            t_clone = t_boot
            print(f"SANDBOX: repo cloned in 0.00s (pre-cloned)")
        else:
            subprocess.run(
                ["docker", "run", "-d", "--name", container_name, "arcane-sandbox", "sleep", "infinity"],
                check=True,
                capture_output=True,
                text=True
            )
            t_boot = time.perf_counter()
            print(f"SANDBOX: container ready in {t_boot - t_start:.2f}s")

            # 2. Clean /sandbox dir in case of leftover files, then clone
            exec_in_container(["sh", "-c", "rm -rf /sandbox/* /sandbox/.*  2>/dev/null || true"])
            clone_res = exec_in_container(["git", "clone", repo_url, "."])
            if clone_res.returncode != 0:
                return {"passed": False, "output": f"Clone failed: {clone_res.stderr}", "exit_code": clone_res.returncode}
            t_clone = time.perf_counter()
            print(f"SANDBOX: repo cloned in {t_clone - t_boot:.2f}s")

            # Install requirements if present
            exec_in_container(["sh", "-c", "test -f requirements.txt && pip install -q -r requirements.txt || true"])


        # 3. Checkout the specific commit SHA — then hard reset for clean state
        exec_in_container(["git", "fetch", "--all"])
        checkout_res = exec_in_container(["git", "checkout", commit_sha])
        if checkout_res.returncode != 0:
            return {"passed": False, "output": f"Checkout failed: {checkout_res.stderr}", "exit_code": checkout_res.returncode}
        exec_in_container(["git", "reset", "--hard", commit_sha])
        exec_in_container(["git", "clean", "-fd"])

        # 4. Apply patch if provided
        if patch_diff:
            patch_res = exec_in_container(["patch", "-p1"], input_str=patch_diff)
            if patch_res.returncode != 0:
                return {"passed": False, "output": f"Patch failed: {patch_res.stderr}", "exit_code": patch_res.returncode}
        
        t_patch = time.perf_counter()
        print(f"SANDBOX: patch applied in {t_patch - t_clone:.2f}s")

        # 5. Inject extra test file into the container if provided
        if extra_test_file and os.path.isfile(extra_test_file):
            dest_name = os.path.basename(extra_test_file)
            subprocess.run(
                ["docker", "cp", extra_test_file, f"{container_name}:/sandbox/tests/{dest_name}"],
                capture_output=True
            )
            print(f"SANDBOX: injected extra test file {dest_name}")

        # 6. Run pytest with a 120-second timeout
        try:
            pytest_res = exec_in_container(["env", "PYTHONPATH=.", "pytest", "-v"], timeout=120)
            t_pytest = time.perf_counter()
            print(f"SANDBOX: pytest done in {t_pytest - t_patch:.2f}s")
            return {
                "passed": pytest_res.returncode == 0,
                "output": pytest_res.stdout + pytest_res.stderr,
                "exit_code": pytest_res.returncode
            }
        except subprocess.TimeoutExpired:
            return {"passed": False, "output": "TIMEOUT", "exit_code": -1}

    except subprocess.CalledProcessError as e:
        return {
            "passed": False,
            "output": f"Docker operation failed: {e.stderr}",
            "exit_code": e.returncode
        }
    except Exception as e:
        return {
            "passed": False,
            "output": f"An unexpected error occurred: {str(e)}",
            "exit_code": 1
        }
    finally:
        # 6. Always remove the container
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        # Re-warm for next call in a background thread
        threading.Thread(target=warm_sandbox, args=(repo_url,)).start()

if __name__ == "__main__":
    pass
