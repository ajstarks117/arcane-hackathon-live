import os
import sys

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.ast_differ import ast_diff

def test_ast_diff_pure_addition():
    file_a = "def old():\n    pass\n"
    file_b = "def old():\n    pass\n\ndef new():\n    return 1\n"
    res = ast_diff(file_a, file_b)
    
    assert "new" in res['added_functions']
    assert "old" not in res['modified_functions']
    assert not res['removed_functions']

def test_ast_diff_pure_deletion():
    file_a = "def old():\n    pass\n\ndef new():\n    return 1\n"
    file_b = "def old():\n    pass\n"
    res = ast_diff(file_a, file_b)
    
    assert "new" in res['removed_functions']
    assert "old" not in res['modified_functions']
    assert not res['added_functions']

def test_ast_diff_modification_and_whitespace_ignore():
    file_a = "def target(a, b):\n    return a + b\n"
    # Modified signature + added whitespace/comments
    file_b = """
def target(a, b, c):
    # This is a comment that should be ignored
    
    return a + b + c
"""
    file_c = """
def target(a, b):
    # Just a comment change, shouldn't mark as modified
    return a + b
"""
    res1 = ast_diff(file_a, file_b)
    assert "target" in res1['modified_functions']
    
    res2 = ast_diff(file_a, file_c)
    assert "target" not in res2['modified_functions']
