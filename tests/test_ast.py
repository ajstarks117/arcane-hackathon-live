import os
import sys

# Add root folder to sys.path so we can import agents
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.ast_parser import parse_python_file

def test_parse_python_file(tmp_path):
    test_file = tmp_path / "sample.py"
    test_file.write_text("""
import os
from math import sqrt

class Calculator:
    pass

def calculate(x):
    return sqrt(x)
""")
    res = parse_python_file(str(test_file))
    
    assert "calculate" in res['functions']
    assert "Calculator" in res['classes']
    assert any("import os" in i for i in res['imports'])
    assert any("from math import sqrt" in i for i in res['imports'])
    assert "tree" in res

def test_parse_demo_repo_auth():
    auth_path = os.path.join(os.path.dirname(__file__), '..', 'arcane-demo-repo', 'auth.py')
    if os.path.exists(auth_path):
        res = parse_python_file(auth_path)
        assert "validate_user" in res['functions']
