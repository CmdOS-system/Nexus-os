"""Reject retired APIs while allowing the two real Tk button test actions."""
import ast
from pathlib import Path
import sys


def violations(source, relative_path):
    tree = ast.parse(source)
    allowed_buttons = {'app.confirm', 'app.open_button'}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'secrets':
            yield node.lineno, 'retired secrets import'
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'invoke':
            is_gui_button = (
                relative_path == 'tests/windows_installer_gui_smoke.py'
                and ast.unparse(node.func.value) in allowed_buttons
                and not node.args and not node.keywords
            )
            if not is_gui_button:
                yield node.lineno, 'retired invoke API'


def main():
    root = Path(sys.argv[1])
    errors = []
    for path in sorted(root.rglob('*.py')):
        if '__pycache__' in path.parts:
            continue
        for line, reason in violations(path.read_text(), path.relative_to(root).as_posix()):
            errors.append(f'{path}:{line}: {reason}')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Legacy security API checks passed (Tk GUI test buttons allowed explicitly)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
