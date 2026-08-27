#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
needle='shared-header.js'
changed=0
for path in ROOT.rglob('*.html'):
    if any(part.startswith('.') for part in path.relative_to(ROOT).parts):
        continue
    text=path.read_text(encoding='utf-8')
    if needle in text:
        continue
    marker='</body>'
    if marker not in text:
        continue
    text=text.replace(marker,'<script src="'+('' if path.parent==ROOT else '../'*len(path.relative_to(ROOT).parent.parts))+'shared-header.js"></script>'+marker,1)
    path.write_text(text,encoding='utf-8')
    changed+=1
print(f'Injected shared UI into {changed} HTML pages')
