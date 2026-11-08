import json
import logging
import os
from typing import Dict, Any
from agents.llm_client import call_llm
from agents.chroma_memory import init_memory, query_memory

logger = logging.getLogger(__name__)

def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the failure log using an LLM to extract key details.
    Retries once with a stricter prompt if the LLM output is not valid JSON.
    """
    failure_log = state.get('failure_log', '')
    
    if not failure_log:
        logger.warning("[Analyst] No failure log provided in state.")
        return state

    # 🧠 CHROMADB MEMORY FAST PATH — check FIRST before any other logic
    try:
        db_path = os.environ.get('CHROMADB_PATH', './chroma_data')
        client = init_memory(db_path)
        # Lower threshold (0.65) because webhook sends commit message, not raw error log
        memory_match = query_memory(client, failure_log, threshold=0.65)

        
        if memory_match:
            try:
                from api.store import store as _store
                if _store.memory_flags.get(memory_match.get("commit_sha"), True) is False:
                    logger.info("[Analyst] Memory match ignored — reuse disabled by a reviewer")
                    memory_match = None
            except Exception:
                pass
        if memory_match:
            patch = memory_match.get("patch_diff", "")
            failing_file = "unknown_file.py"
            # Extract filename from patch header (e.g., --- a/api/auth.py)
            for line in patch.splitlines():
                if line.startswith("--- a/"):
                    failing_file = line[6:].strip()
                    break

            invalid_placeholders = {
                "unknown_file", "unknown_file.py", "unknown", "", None,
                "n/a", "na", "n/a.", "none", "not available", "not_available"
            }
            commit_sha = str(memory_match.get("commit_sha", ""))
            if (
                not patch
                or not patch.strip()
                or failing_file.strip().lower() in invalid_placeholders
                or commit_sha.startswith("manual")
            ):
                logger.info(
                    f"[Analyst] Memory match discarded because patch, failing_file '{failing_file}', or commit '{commit_sha}' is invalid."
                )
                memory_match = None
            else:
                logger.info(
                    f"[Analyst] 🧠 CHROMA MEMORY HIT! Bypassing LLM analysis. Matched commit: {commit_sha}"
                )
                return {
                    **state,
                    "memory_hit": memory_match,  # Store for PR agent
                    "failing_test": memory_match.get("test_file", "unknown_test"),
                    "failing_file": failing_file,
                    "failing_line": 0,
                    "root_cause_summary": memory_match.get("root_cause", ""),
                    "patch_diff": patch,
                    "fast_forward_patch": True,
                }
    except Exception as e:
        logger.error(f"[Analyst] ChromaDB memory check failed: {e}")

    system_prompt = (
        "You are an expert CI/CD failure analyst. Analyze the provided test failure log "
        "and extract the required information. You must respond ONLY with a valid JSON object. "
        "Do not include any preamble, explanations, or markdown fences (like ```json). "
        "The JSON object must have exactly these keys: "
        "\"failing_test\" (string), \"failing_file\" (string), \"failing_line\" (integer), "
        "\"root_cause_summary\" (string - max 2 sentences), \"suspected_function\" (string)."
    )

    prompt = f"Here is the failure log:\n\n{failure_log}"
    
    logger.info("[Analyst] Calling LLM to parse failure log...")
    response_text = call_llm(prompt=prompt, system=system_prompt)
    
    try:
        # First attempt to parse JSON
        parsed_data = json.loads(response_text.strip())
        logger.info("[Analyst] Successfully parsed JSON on first attempt.")
    except json.JSONDecodeError:
        logger.warning("[Analyst] Failed to parse JSON. Retrying with stricter prompt...")
        
        strict_system_prompt = (
            "You failed to return valid JSON previously. "
            "Return ONLY a raw JSON object. No text before or after it. No markdown code fences. "
            "The JSON object must have exactly these keys: "
            "\"failing_test\" (string), \"failing_file\" (string), \"failing_line\" (integer), "
            "\"root_cause_summary\" (string), \"suspected_function\" (string)."
        )
        
        response_text = call_llm(prompt=prompt, system=strict_system_prompt)
        
        try:
            # Second attempt
            # Try to strip any potential accidental markdown if the LLM still messed up
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
                
            parsed_data = json.loads(clean_text)
            logger.info("[Analyst] Successfully parsed JSON on retry.")
        except json.JSONDecodeError as e:
            logger.error(f"[Analyst] Failed to parse JSON on retry. Error: {e}")
            logger.error(f"Raw LLM response: {response_text}")
            # Return original state if we completely fail, to not break the pipeline
            return state

    failing_file = parsed_data.get("failing_file", "")
    failing_test = parsed_data.get("failing_test", "")

    # If LLM couldn't extract a real failing file, do not fabricate demo data
    placeholder_values = {
        "unknown_file", "unknown_file.py", "unknown", "", None,
        "N/A", "n/a", "na", "N/A.", "none", "None",
        "not available", "not_available", "unknown test", "unknown_test"
    }
    normalized_placeholders = {p.lower() for p in placeholder_values if p}
    if not failing_file or failing_file.strip().lower() in normalized_placeholders:
        logger.warning(f"[Analyst] LLM could not extract a valid failing_file from log: '{failing_file}'")
        return {
            **state,
            "error": f"Analyst could not identify a real failing file from the provided failure log (got '{failing_file}').",
            "failing_file": "",
            "failing_test": failing_test or "",
        }

    # Update state with the extracted fields
    return {
        **state,
        "failing_test": failing_test,
        "failing_file": failing_file,
        "failing_line": parsed_data.get("failing_line", 0),
        "root_cause_summary": parsed_data.get("root_cause_summary", "Could not determine root cause."),
        "suspected_function": parsed_data.get("suspected_function", "unknown_function"),
    }
