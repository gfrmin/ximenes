"""DESIGN D2/C6: no execution, no network, no I/O surprises in the kernel."""

import ast
import pathlib
import sys

FORBIDDEN_CALLS = {"exec", "eval", "compile", "__import__", "open"}
FORBIDDEN_MODULES = {
    "subprocess", "importlib", "pickle", "socket", "urllib", "requests",
    "httpx", "anthropic", "openai", "os", "shutil",
}
# Modules allowed to do I/O and network, by file stem.
IO_ALLOWED = {"instruments", "data", "eval"}


def check(path: pathlib.Path) -> list[str]:
    tree = ast.parse(path.read_text())
    errors = []
    allowed_io = path.stem in IO_ALLOWED
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [(node.module or "").split(".")[0]]
            for n in names:
                if n in FORBIDDEN_MODULES and not allowed_io:
                    errors.append(f"{path}:{node.lineno}: import {n}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS and not (allowed_io and node.func.id == "open"):
                errors.append(f"{path}:{node.lineno}: call {node.func.id}()")
    return errors


def main() -> int:
    root = pathlib.Path(sys.argv[1])
    errors = [e for p in root.rglob("*.py") for e in check(p)]
    for e in errors:
        print("RED:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
