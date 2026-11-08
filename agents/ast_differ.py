import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import os

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

def _get_function_nodes(root_node):
    funcs = {}
    
    def traverse(node):
        if node.type == 'function_definition':
            name_node = None
            for child in node.children:
                if child.type == 'identifier':
                    name_node = child
                    break
            if name_node:
                name = name_node.text.decode('utf8')
                
                # Clean comment nodes and normalize whitespace
                body_text = ""
                for child in node.children:
                    if child.type != 'comment':
                        body_text += child.text.decode('utf8') + " "
                
                normalized = " ".join(body_text.split())
                funcs[name] = normalized
        for child in node.children:
            traverse(child)
            
    traverse(root_node)
    return funcs

def _get_imports(root_node):
    imports = []
    def traverse(node):
        if node.type in ['import_statement', 'import_from_statement']:
            imports.append(node.text.decode('utf8').strip())
        for child in node.children:
            traverse(child)
    traverse(root_node)
    return set(imports)

def ast_diff(file_a: str, file_b: str) -> dict:
    def read_src(path_or_str):
        try:
            if os.path.exists(path_or_str):
                with open(path_or_str, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read().encode("utf8")
        except OSError:
            pass
        return path_or_str.encode("utf8")
        
    src_a = read_src(file_a)
    src_b = read_src(file_b)
    
    tree_a = parser.parse(src_a)
    tree_b = parser.parse(src_b)
    
    if tree_a.root_node.has_error or tree_b.root_node.has_error:
        print("Warning: AST diff detected syntax error in files.")
        
    funcs_a = _get_function_nodes(tree_a.root_node)
    funcs_b = _get_function_nodes(tree_b.root_node)
    
    imports_a = _get_imports(tree_a.root_node)
    imports_b = _get_imports(tree_b.root_node)
    
    added_functions = list(set(funcs_b.keys()) - set(funcs_a.keys()))
    removed_functions = list(set(funcs_a.keys()) - set(funcs_b.keys()))
    
    modified_functions = []
    for func, text_a in funcs_a.items():
        if func in funcs_b and funcs_b[func] != text_a:
            modified_functions.append(func)
            
    added_imports = list(imports_b - imports_a)
    removed_imports = list(imports_a - imports_b)
    
    return {
        'added_functions': added_functions,
        'removed_functions': removed_functions,
        'modified_functions': modified_functions,
        'added_imports': added_imports,
        'removed_imports': removed_imports,
    }
