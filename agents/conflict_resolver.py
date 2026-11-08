"""
conflict_resolver.py
====================
Single entry point for the CONFLICT_CHECKING LangGraph node.

Usage (Ajinkya's orchestrator):
    from agents.conflict_resolver import ConflictResolver
    result = ConflictResolver().check(state)

Returns a dict added directly to LangGraph state:
    {
        'conflicts_found': bool,
        'action':  'auto_resolved' | 'escalated' | 'needs_review' | 'no_conflict',
        'confidence_score': float,
        'details': list[dict]   # one entry per conflict block
    }
"""

from agents.conflict_detector import detect_conflicts
from agents.ast_differ import ast_diff
from agents.intent_inferrer import infer_intent
from agents.confidence_scorer import score_resolution
from agents.auto_resolver import resolve


class ConflictResolver:
    def check(self, state: dict, github_repo=None) -> dict:
        """
        Main entry point called by the CONFLICT_CHECKING LangGraph node.

        Expects state to contain:
            state['failing_file']       — path to the file being checked
            state['ours_commit_msg']    — commit message of our version
            state['theirs_commit_msg']  — commit message of their version
            state['commit_sha']         — current commit SHA (for GitHub comments)

        Returns a dict to merge back into LangGraph state.
        """
        filepath        = state.get('failing_file', '')
        ours_msg        = state.get('ours_commit_msg', 'ours change')
        theirs_msg      = state.get('theirs_commit_msg', 'theirs change')
        commit_sha      = state.get('commit_sha', '')

        # ── Step 1: detect conflict markers ──────────────────────────────────
        conflicts = detect_conflicts(filepath)

        if not conflicts:
            return {
                'conflicts_found': False,
                'action': 'no_conflict',
                'confidence_score': 1.0,
                'details': []
            }

        # ── Step 2: process each conflict block ───────────────────────────────
        details = []
        overall_action = 'auto_resolved'   # escalate if any block requires it
        lowest_score   = 1.0

        for conflict in conflicts:
            ours_code   = conflict['ours']
            theirs_code = conflict['theirs']

            # AST diff on the two code snippets
            diff_result = ast_diff(ours_code, theirs_code)

            # Ask LLM which version wins
            intent = infer_intent(
                ours_code, theirs_code,
                ours_msg, theirs_msg
            )

            # Score the resolution
            score = score_resolution(intent, diff_result)

            # Resolve (writes file in-place if high confidence)
            resolution = resolve(
                conflict, intent, score,
                github_repo=github_repo,
                commit_sha=commit_sha
            )

            details.append({
                'conflict':   conflict,
                'intent':     intent,
                'score':      score,
                'resolution': resolution
            })

            # Track the worst outcome across all blocks
            if score < lowest_score:
                lowest_score = score

            # Escalation takes priority over everything
            if resolution['action'] == 'escalated':
                overall_action = 'escalated'
            elif resolution['action'] == 'needs_review' and overall_action != 'escalated':
                overall_action = 'needs_review'

        return {
            'conflicts_found': True,
            'action':          overall_action,
            'confidence_score': lowest_score,
            'details':         details
        }
