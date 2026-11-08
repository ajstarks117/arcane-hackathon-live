"""
cross_file_propagator.py
========================
Single entry point for the PROPAGATING LangGraph node (Ajinkya's orchestrator).

Usage:
    from agents.cross_file_propagator import CrossFilePropagator
    result = CrossFilePropagator().propagate(state)
"""

from agents.dep_graph_builder import build_dep_graph
from agents.caller_finder import find_callers
from agents.multi_file_patcher import generate_caller_patches


class CrossFilePropagator:
    def __init__(self):
        self._graph_cache: dict | None = None
        self._cached_repo: str = ''

    def propagate(self, state: dict) -> dict:
        """
        Main entry point for the PROPAGATING LangGraph node.

        Expects state to contain:
            state['repo_path']           — absolute path to the repo
            state['changed_function']    — name of the function that was patched
            state['original_signature']  — old call signature string
            state['new_signature']       — new call signature string

        Returns dict to merge into LangGraph state:
            {
                'propagated_files': ['api.py', 'middleware.py'],
                'caller_patches':   [{'file': ..., 'patch': ...}, ...],
                'propagation_done': bool
            }
        """
        repo_path          = state.get('repo_path', '')
        changed_function   = state.get('changed_function', '')
        original_signature = state.get('original_signature', changed_function)
        new_signature      = state.get('new_signature', changed_function)

        # ── Step 1: Build (or reuse cached) dependency graph ─────────────────
        if self._cached_repo != repo_path or self._graph_cache is None:
            self._graph_cache = build_dep_graph(repo_path)
            self._cached_repo = repo_path

        # ── Step 2: Find all caller files ────────────────────────────────────
        callers = find_callers(changed_function, self._graph_cache)

        if not callers:
            return {
                'propagated_files': [],
                'caller_patches':   [],
                'propagation_done': True
            }

        # ── Step 3: Generate patches for each caller ──────────────────────────
        patches = generate_caller_patches(
            callers,
            original_signature,
            new_signature,
            repo_path=repo_path
        )

        return {
            'propagated_files': callers,
            'caller_patches':   patches,
            'propagation_done': True
        }
