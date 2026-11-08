"""
ARCANE Validator Integration Patch for Ajinkya's orchestrator.py

HOW TO USE:
  Replace the bodies of `validating_node` and `generating_test_node` in
  agents/orchestrator.py with the implementations below.

  Also add `capture_baseline(state)` call at the END of `idle_node`.

IMPORTS TO ADD at the top of orchestrator.py:
    from agents.validator_agent import validate, capture_baseline
    from agents.regression_test_generator import generate_regression_test
"""

# ──────────────────────────────────────────────────────────────────────────────
# 1. IDLE NODE ADDITION
#    Add this line at the end of idle_node(), inside the return dict:
# ──────────────────────────────────────────────────────────────────────────────

IDLE_NODE_ADDITION = """
    # Call capture_baseline to record which tests pass/fail BEFORE any patch
    state_with_baseline = capture_baseline({
        **state,
        "repo_full_name": event.get("repo_full_name", state.get("repo_full_name", "")),
        "commit_sha":     event.get("commit_sha", state.get("commit_sha", "")),
        "failure_log":    event.get("failure_log", state.get("failure_log", "")),
    })
    return state_with_baseline
"""

# ──────────────────────────────────────────────────────────────────────────────
# 2. VALIDATING NODE  (replaces the mock body)
# ──────────────────────────────────────────────────────────────────────────────

VALIDATING_NODE = """
def validating_node(state: ArcaneState) -> ArcaneState:
    \"\"\"VALIDATING — applies patch in Docker sandbox and runs full pytest suite.\"\"\"
    retry = state.get("retry_count", 0)
    logger.info(f"[VALIDATING] Running test suite (attempt {retry + 1})")
    updated = validate(state)
    return {**state, **updated}
"""

# ──────────────────────────────────────────────────────────────────────────────
# 3. GENERATING_TEST NODE  (replaces the hardcoded mock body)
# ──────────────────────────────────────────────────────────────────────────────

GENERATING_TEST_NODE = """
def generating_test_node(state: ArcaneState) -> ArcaneState:
    \"\"\"GENERATING_TEST — uses Claude LLM to synthesize a regression test.\"\"\"
    logger.info("[GENERATING_TEST] Producing regression test via LLM")
    updated = generate_regression_test(state)
    return {**state, **updated}
"""

# ──────────────────────────────────────────────────────────────────────────────
# SUMMARY OF STATE KEYS ADDED BY VALIDATOR MODULE
# ──────────────────────────────────────────────────────────────────────────────
STATE_KEYS = {
    # From capture_baseline() — set in IDLE node
    "baseline_passing_tests":  "list[str]  — test paths passing before any patch",
    "baseline_failing_tests":  "list[str]  — test paths already failing (known broken)",

    # From validate() — set in VALIDATING node
    "tests_passed":            "bool       — True only if exit_code==0 AND no cascade",
    "test_output":             "str        — full pytest stdout+stderr",
    "validator_exit_code":     "int        — raw pytest exit code",
    "validator_summary":       "str        — one-liner for PR body",
    "retry_count":             "int        — increments on every failure",
    "timeout":                 "bool       — True if sandbox timed out (120s)",
    "cascade_failure":         "bool       — True if patch broke previously-passing tests",
    "cascade_failure_report":  "list[str]  — names of newly broken tests",
    "cascade_context":         "str        — ready-made retry prompt for Patch Generator",

    # From generate_regression_test() — set in GENERATING_TEST node
    "regression_test_code":   "str        — synthesized pytest function",
    "regression_test_file":   "str        — path to /tmp/arcane_regtest_*.py",
}

if __name__ == "__main__":
    print("=== ARCANE Validator Integration Guide ===\n")
    print("VALIDATING node replacement:\n")
    print(VALIDATING_NODE)
    print("\nGENERATING_TEST node replacement:\n")
    print(GENERATING_TEST_NODE)
    print("\nIDLE node addition:\n")
    print(IDLE_NODE_ADDITION)
    print("\nState keys added by Validator module:")
    for k, v in STATE_KEYS.items():
        print(f"  {k:<30} {v}")
