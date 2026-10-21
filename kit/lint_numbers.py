"""DESIGN D5: no numeric literal in kernel code except 0 and 1.

Numbers belong in data tables with a `source`. Files listed in ALLOW may use
other literals (e.g. regex group indices, bin counts under a comment naming
the table they mirror)."""

import ast
import pathlib
import sys

ALLOWED_VALUES = {0, 1}
ALLOW = {"clue.py"}  # regex group indices only; reviewed


def check(path: pathlib.Path) -> list[str]:
    if path.name in ALLOW:
        return []
    tree = ast.parse(path.read_text())
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if isinstance(node.value, bool) or node.value in ALLOWED_VALUES:
                continue
            out.append(f"{path}:{node.lineno}: numeric literal {node.value!r}")
    return out


def main() -> int:
    root = pathlib.Path(sys.argv[1])
    errors = [e for p in root.rglob("*.py") for e in check(p)]
    for e in errors:
        print("RED:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
