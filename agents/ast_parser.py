import tree_sitter_python as tspython
from tree_sitter import Language, Parser

def parse_python_file(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        src = f.read()

    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(bytes(src, "utf8"))
    
    functions = []
    imports = []
    classes = []
    
    def traverse(node):
        if node.type == 'function_definition':
            for child in node.children:
                if child.type == 'identifier':
                    functions.append(child.text.decode('utf8'))
        elif node.type == 'class_definition':
            for child in node.children:
                if child.type == 'identifier':
                    classes.append(child.text.decode('utf8'))
        elif node.type in ['import_statement', 'import_from_statement']:
            imports.append(node.text.decode('utf8').strip())
            
        for child in node.children:
            traverse(child)

    traverse(tree.root_node)

    return {
        'functions': functions,
        'imports': imports,
        'classes': classes,
        'tree': tree
    }

if __name__ == "__main__":
    import sys
    res = parse_python_file(sys.argv[0])
    print("Functions:", res['functions'])
    print("Imports:", res['imports'])
    print("Classes:", res['classes'])
