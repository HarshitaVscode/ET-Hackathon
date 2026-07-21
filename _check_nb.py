import json

with open('backend/src/hyperlocal_forecast_agent/notebooks/hyperlocal_forecast_agent.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

errors = []
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])
        if not src.strip():
            continue
        try:
            compile(src, f'<cell_{i}>', 'exec')
        except SyntaxError as e:
            errors.append((i, str(e), src[:100]))

code_cells = sum(1 for c in nb['cells'] if c['cell_type'] == 'code')
if errors:
    for idx, err, src in errors:
        print(f'Cell {idx}: {err}')
else:
    print(f'All {code_cells} code cells compile OK')
