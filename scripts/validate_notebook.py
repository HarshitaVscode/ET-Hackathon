"""Validate the generated notebook."""
import ast, json, sys
from pathlib import Path

nb = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
errors = []
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        src = "".join(cell["source"])
        src_clean = src.replace("%matplotlib inline", "# matplotlib inline")
        try:
            ast.parse(src_clean)
        except SyntaxError as e:
            errors.append((i + 1, str(e)))

if errors:
    for num, msg in errors:
        print(f"Cell {num}: {msg}")
    sys.exit(1)
else:
    print(f"OK: All {len(nb['cells'])} cells pass ast.parse()")
