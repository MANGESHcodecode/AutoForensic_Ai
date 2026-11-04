import re
from pathlib import Path

js_path = Path("web/static/js/dashboard.js")
html_path = Path("web/templates/index.html")

js_text = js_path.read_text(encoding="utf-8")
html_text = html_path.read_text(encoding="utf-8")

js_ids = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', js_text))
html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html_text))

missing = js_ids - html_ids
print("Total IDs referenced in JS:", len(js_ids))
print("Missing IDs in HTML:", missing)
for m in missing:
    lines = [i+1 for i, line in enumerate(js_text.splitlines()) if m in line]
    print(f"  '{m}' is used on lines: {lines}")
