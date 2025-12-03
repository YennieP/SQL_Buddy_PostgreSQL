import os
from pathlib import Path

def print_tree(directory, prefix="", ignore_dirs=None, max_depth=3, current_depth=0):
    """打印目录树结构"""
    if ignore_dirs is None:
        ignore_dirs = {'__pycache__', 'venv', 'dbenv', '.git', 'node_modules', '.vscode'}
    
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(Path(directory).iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        return
    
    pointers = []
    for i, item in enumerate(items):
        if item.name in ignore_dirs or item.name.startswith('.'):
            continue
            
        pointers.append(item)
    
    for i, item in enumerate(pointers):
        is_last = i == len(pointers) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir():
            next_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(item, next_prefix, ignore_dirs, max_depth, current_depth + 1)

if __name__ == "__main__":
    print("sqlbuddy/")
    print_tree(".", max_depth=4)