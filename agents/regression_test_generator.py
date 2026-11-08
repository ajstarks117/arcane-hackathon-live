import os
import subprocess
import json
import tempfile
from typing import Dict, Any
from agents.sandbox_runner import run_sandbox
from agents.llm_client import call_llm

def generate_regression_test(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a pytest regression test using an LLM based on the root cause and patch.
    """
    root_cause_summary = state.get("root_cause_summary", "Unknown root cause")
    patch_diff = state.get("patch_diff", "")
    failing_file = state.get("failing_file", "unknown_file.py")
    commit_sha = state.get("commit_sha", "unknown")
    
    failing_file_stem = failing_file.replace("/", "_").replace(".py", "")

    system_prompt = (
        "You are an expert Python test engineer. Return ONLY valid pytest code. "
        "No preamble, no markdown, no explanation. Just the test function starting with 'def test_'. "
        "Do not use markdown. Do not use backticks. "
        "The function must include a docstring as its first statement."
    )
    
    user_prompt = f"""Root cause: {root_cause_summary}
Patch applied to {failing_file}:
{patch_diff}

Write a pytest function named test_{failing_file_stem}_regression that:
- Would FAIL on the original buggy code
- Would PASS on the patched code
- Tests the exact scenario described in the root cause
- Is standalone: no fixtures, minimal imports
- Includes a docstring: "Regression test for: {root_cause_summary}"
Return only the function. No class wrapper."""

    print("Generating regression test via LLM...")
    generated_code = call_llm(prompt=user_prompt, system=system_prompt)
    
    # Post-processing: strip markdown backticks if LLM disobeyed
    cleaned_code = ""
    for line in generated_code.splitlines():
        if not line.strip().startswith("```"):
            cleaned_code += line + "\n"
    
    regression_test_code = cleaned_code.strip()
    
    # Fallback if no docstring
    if '"""' not in regression_test_code and "'''" not in regression_test_code:
        print("Warning: Generated test has no docstring. Retrying once...")
        system_prompt += " YOU MUST INCLUDE A DOCSTRING AS THE FIRST STATEMENT IN THE FUNCTION."
        generated_code = call_llm(prompt=user_prompt, system=system_prompt)
        cleaned_code = ""
        for line in generated_code.splitlines():
            if not line.strip().startswith("```"):
                cleaned_code += line + "\n"
        regression_test_code = cleaned_code.strip()

    # Write to file
    sha_short = commit_sha[:7] if commit_sha else "unknown"
    test_file_path = os.path.join(tempfile.gettempdir(), f"arcane_regtest_{sha_short}.py")
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(regression_test_code)
        
    print(f"Regression test generated and saved to {test_file_path}")
    
    state["regression_test_code"] = regression_test_code
    state["regression_test_file"] = test_file_path
    
    return state


def validate_regression_test(state: dict, retry: int = 0) -> dict:
    """
    Validates the generated regression test:
      1. Syntax check (fast, local)
      2. Semantic: must FAIL on original broken code
      3. Semantic: must PASS on patched code
    Retries generation once with a stricter prompt if any check fails.
    """
    test_file_path = state.get("regression_test_file", "")
    patch_diff     = state.get("patch_diff", "")
    repo_full_name = state.get("repo_full_name", "")
    commit_sha     = state.get("commit_sha", "")
    repo_url       = f"https://github.com/{repo_full_name}" if repo_full_name else ""

    def _fail(reason: str) -> dict:
        if retry < 1:
            print(f"REGTEST RETRY — reason: {reason}. Regenerating with stricter prompt...")
            # Inject failure reason into state for stricter prompt
            state["regtest_error"] = reason
            state["regtest_retry_hint"] = (
                f"Previous attempt failed validation: {reason}. "
                "Be extra careful. The test MUST fail on the original code and pass on the patched code."
            )
            regenerated = generate_regression_test(state)
            return validate_regression_test(regenerated, retry=1)
        print(f"REGTEST SKIPPED — second attempt also failed: {reason}")
        state["regtest_valid"] = False
        state["regtest_error"] = reason
        return state

    # ── 1. SYNTAX CHECK ────────────────────────────────────────────────────
    if not test_file_path or not os.path.isfile(test_file_path):
        return _fail("SYNTAX_ERROR: test file not found")

    syntax_res = subprocess.run(
        ["python", "-m", "py_compile", test_file_path],
        capture_output=True, text=True
    )
    if syntax_res.returncode != 0:
        print(f"REGTEST SYNTAX ERROR:\n{syntax_res.stderr}")
        return _fail("SYNTAX_ERROR")

    print("REGTEST: syntax check passed")

    # ── 2. SEMANTIC: must FAIL on broken code (no patch) ──────────────────
    result_broken = run_sandbox(
        repo_url, commit_sha,
        patch_diff=None,
        extra_test_file=test_file_path
    )
    if result_broken["exit_code"] == 0:
        return _fail("TEST_DOES_NOT_CATCH_BUG")

    print("REGTEST: correctly fails on broken code ✓")

    # ── 3. SEMANTIC: must PASS on patched code ─────────────────────────────
    result_patched = run_sandbox(
        repo_url, commit_sha,
        patch_diff=patch_diff,
        extra_test_file=test_file_path
    )
    if result_patched["exit_code"] != 0:
        return _fail("TEST_FAILS_ON_FIX")

    print("REGTEST: correctly passes on patched code ✓")

    # ── All checks passed ──────────────────────────────────────────────────
    state["regtest_valid"] = True
    state.pop("regtest_error", None)
    print("REGTEST VALID — regression test accepted")
    return state

