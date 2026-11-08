import os
import json
import httpx
from agents.llm_client import call_llm

def infer_intent(ours_code: str, theirs_code: str,
                 ours_commit_msg: str, theirs_commit_msg: str) -> dict:
    
    prompt = f"""You are a senior software engineer reviewing a Git merge conflict.

OURS (commit: "{ours_commit_msg}"):
```python
{ours_code}
```

THEIRS (commit: "{theirs_commit_msg}"):
```python
{theirs_code}
```

Answer the following:
1. Which change better represents the intended system behavior?
2. Are these changes compatible or mutually exclusive?

Return ONLY a JSON object with no preamble, no markdown fences, exactly this shape:
{{"winner": "ours" | "theirs" | "merge", "reasoning": "one sentence explanation", "compatible": true | false, "confidence": 0.0}}"""

    try:
        result = call_llm(prompt)
        return _parse_response(result)
    except Exception as e:
        print(f"LLM intent inference failed: {e}. Returning safe default.")
        return {
            "winner": "ours",
            "reasoning": "Could not infer intent — defaulting to ours.",
            "compatible": False,
            "confidence": 0.5
        }

def _parse_response(text: str) -> dict:
    # Strip markdown fences if present
    cleaned = text.replace("```json", "").replace("```", "").strip()
    
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Retry: extract first {...} block
        import re
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse LLM response as JSON: {cleaned}")
    
    # Defensive type coercions
    result['confidence'] = float(result.get('confidence', 0.5))
    result['compatible'] = bool(result.get('compatible', False))
    result.setdefault('winner', 'ours')
    result.setdefault('reasoning', '')
    
    return result
