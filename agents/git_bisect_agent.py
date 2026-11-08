import os
import re
import json
import uuid
import time
import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def run_bisect(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automates the process of finding the commit that introduced a failure using git bisect.
    Runs entirely inside an isolated Docker sandbox.
    """
    repo_full_name = state.get("repo_full_name", "")
    target_commit_sha = state.get("commit_sha", "")
    
    if not repo_full_name or not target_commit_sha:
        logger.error("[Bisect] Missing repo_full_name or commit_sha in state.")
        return {**state, "bisect_intent_report": "Error: Missing repo info for bisect."}

    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        logger.warning("[Bisect] GITHUB_PAT not set. Cloning might fail if the repo is private.")
        repo_url = f"https://github.com/{repo_full_name}.git"
    else:
        repo_url = f"https://x-access-token:{github_pat}@github.com/{repo_full_name}.git"

    container_name = f"arcane-bisect-{uuid.uuid4().hex[:8]}"
    logger.info(f"[Bisect] Booting sandbox container: {container_name}")
    
    # 1. Boot the container
    try:
        subprocess.run(
            ["docker", "run", "-d", "--name", container_name, "--memory", "2g", "arcane-sandbox", "sleep", "infinity"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"[Bisect] Failed to boot container: {e.stderr}")
        return {**state, "bisect_intent_report": "Error: Failed to boot sandbox."}

    def exec_cmd(cmd_list, timeout=60):
        """Helper to run a command inside the sandbox."""
        return subprocess.run(
            ["docker", "exec", "-i", container_name] + cmd_list,
            capture_output=True,
            text=True,
            timeout=timeout
        )

    try:
        # Set up git config to prevent bisect errors
        exec_cmd(["git", "config", "--global", "user.email", "arcane@bot.ai"])
        exec_cmd(["git", "config", "--global", "user.name", "ARCANE Bot"])

        # 2. Clone the repo shallowly
        logger.info(f"[Bisect] Cloning repository {repo_full_name}...")
        clone_res = exec_cmd(["git", "clone", repo_url, "."])
        if clone_res.returncode != 0:
            raise RuntimeError(f"Clone failed: {clone_res.stderr}")

        # 3. Initialize Bisect
        # First, ensure we are on the target failing commit
        checkout_res = exec_cmd(["git", "checkout", target_commit_sha])
        if checkout_res.returncode != 0:
            raise RuntimeError(f"Failed to checkout target commit {target_commit_sha}: {checkout_res.stderr}")

        exec_cmd(["git", "bisect", "start"])
        exec_cmd(["git", "bisect", "bad"])  # HEAD (target_commit_sha) is bad

        # Read known good commit from .arcane_config.json
        known_good_commit = None
        cat_res = exec_cmd(["cat", ".arcane_config.json"])
        if cat_res.returncode == 0:
            try:
                config = json.loads(cat_res.stdout)
                known_good_commit = config.get("known_good_commit")
            except Exception as e:
                logger.warning(f"Failed to parse .arcane_config.json: {e}")
                
        if not known_good_commit:
            logger.info("[Bisect] .arcane_config.json missing or invalid. Falling back to HEAD~3 as known good commit.")
            head_3_res = exec_cmd(["git", "rev-parse", "HEAD~3"])
            if head_3_res.returncode == 0:
                known_good_commit = head_3_res.stdout.strip()
            else:
                raise RuntimeError("Failed to resolve HEAD~3 for bisect fallback.")

        logger.info(f"[Bisect] Found known good commit: {known_good_commit[:7]}")
        
        # Check if known_good_commit is in our shallow history
        check_commit_res = exec_cmd(["git", "rev-parse", "--verify", f"{known_good_commit}^{{commit}}"])
        if check_commit_res.returncode != 0:
            logger.info(f"[Bisect] Commit {known_good_commit[:7]} not in shallow history. Fetching --unshallow...")
            unshallow_res = exec_cmd(["git", "fetch", "--unshallow"])
            if unshallow_res.returncode != 0:
                logger.warning(f"[Bisect] Unshallow fetch failed: {unshallow_res.stderr}")

        logger.info(f"[Bisect] Marking {known_good_commit[:7]} as good.")
        good_res = exec_cmd(["git", "bisect", "good", known_good_commit])
        if good_res.returncode != 0:
            raise RuntimeError(f"Failed to mark {known_good_commit} as good: {good_res.stderr}")

        # 4. The Bisect Loop
        MAX_ITERATIONS = 8
        bad_commit_found = None
        bisect_output = good_res.stdout + good_res.stderr

        for i in range(MAX_ITERATIONS):
            logger.info(f"[Bisect] Iteration {i+1}/{MAX_ITERATIONS}...")
            
            # Run pytest
            pytest_res = exec_cmd(["env", "PYTHONPATH=.", "pytest", "-v"])
            
            if pytest_res.returncode == 0:
                logger.info("[Bisect] Tests passed. Marking current commit as GOOD.")
                step_res = exec_cmd(["git", "bisect", "good"])
            else:
                logger.info("[Bisect] Tests failed. Marking current commit as BAD.")
                step_res = exec_cmd(["git", "bisect", "bad"])

            bisect_output = step_res.stdout + step_res.stderr
            
            # Check if the bad commit was found
            if "is the first bad commit" in bisect_output:
                # Extract the SHA
                # Output usually looks like: <sha> is the first bad commit
                match = re.search(r"([0-9a-f]{40})\s+is the first bad commit", bisect_output)
                if match:
                    bad_commit_found = match.group(1)
                else:
                    # Fallback extraction
                    lines = bisect_output.strip().splitlines()
                    for line in lines:
                        if "is the first bad commit" in line:
                            bad_commit_found = line.split()[0]
                            break
                break

        # 5. Build Intent Report
        if bad_commit_found:
            logger.info(f"[Bisect] Found first bad commit: {bad_commit_found[:7]}")
            
            # Get commit metadata
            log_res = exec_cmd(["git", "log", "-1", "--format=%H%n%an%n%s%n%b", bad_commit_found])
            log_parts = log_res.stdout.strip().split("\n", 3)
            commit_hash = log_parts[0] if len(log_parts) > 0 else bad_commit_found
            author = log_parts[1] if len(log_parts) > 1 else "Unknown"
            subject = log_parts[2] if len(log_parts) > 2 else "No Subject"
            body = log_parts[3] if len(log_parts) > 3 else ""

            # Get full diff
            show_res = exec_cmd(["git", "show", bad_commit_found])
            diff_output = show_res.stdout.strip()

            intent_report = (
                f"Bisect identified commit {commit_hash[:7]} as the first bad commit.\n"
                f"Author: {author}\n"
                f"Message: {subject}\n"
                f"Body: {body}\n\n"
                f"--- Diff ---\n{diff_output}\n"
            )
        else:
            logger.warning("[Bisect] Max iterations reached without finding the exact bad commit.")
            state["bisect_confidence"] = "low"
            # Get the current HEAD as best guess
            head_res = exec_cmd(["git", "rev-parse", "HEAD"])
            best_guess = head_res.stdout.strip()
            
            show_res = exec_cmd(["git", "show", best_guess])
            diff_output = show_res.stdout.strip()
            
            intent_report = (
                f"[LOW CONFIDENCE] Bisect exhausted {MAX_ITERATIONS} iterations. "
                f"Best guess for bad commit is {best_guess[:7]}.\n\n"
                f"--- Diff ---\n{diff_output}\n"
            )

        return {**state, "bisect_intent_report": intent_report}

    except Exception as e:
        logger.error(f"[Bisect] Sandbox error: {e}")
        return {**state, "bisect_intent_report": f"Error during bisect: {e}"}
        
    finally:
        # 6. Cleanup container
        logger.info(f"[Bisect] Cleaning up container {container_name}")
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
