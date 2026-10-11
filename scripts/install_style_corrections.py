#!/usr/bin/env python3
"""Install visually reviewed style edits, preserving artwork URLs and display ratios."""
import hashlib
import json
import os
import re
from pathlib import Path
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE)
records = ROOT / 'docs/tasks/artwork-style-correction-results'
version_path = ROOT / 'app/src/data/schoolArtworkVersions.js'
layout_path = ROOT / 'app/src/data/heroArtworkLayout.js'
versions = json.loads(re.search(r'= (\{.*\});', version_path.read_text(), re.S).group(1))
layout = layout_path.read_text()
match = re.search(r'const dimensions = (\{[^\n]+\});', layout)
dimensions = json.loads(match.group(1))
installed = []
for record in sorted(records.glob('style-*.json')):
    row = json.loads(record.read_text())
    if row['status'] not in ('reviewed', 'installed'):
        continue
    target = ROOT / 'app/public' / row['image'].lstrip('/')
    before_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    if row['status'] == 'installed':
        assert before_hash == row['installedSha256'], row['name']
    else:
        assert before_hash == row['sha256'], ('Asset changed since audit', row['name'])
        image = Image.open(row['source']).convert('RGB')
        size = (1440, 1080) if row['group'] == '八学科入口图' else (1600, 900)
        assert abs(image.width / image.height - size[0] / size[1]) < .01, (row['name'], image.size)
        row['generatedDimensions'] = list(image.size)
        # Format conversion and subpixel aspect rounding only; creative edits are image_gen outputs.
        image.resize(size, Image.Resampling.LANCZOS).save(target, 'WEBP', quality=88, method=6)
        row['installedDimensions'] = list(size)
        row['installedSha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        row['status'] = 'installed'
        row['publication'] = 'pending'
        record.write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
    versions[row['image']] = row['installedSha256'][:12]
    dimensions[row['image']] = row['installedDimensions']
    installed.append({'id':row['id'], 'name':row['name'], 'image':row['image'], 'source':row['source'], 'dimensions':row['installedDimensions'], 'sha256':row['installedSha256']})
version_path.write_text('// Content hashes for artwork replacements; canonical public paths stay unchanged.\nexport const SCHOOL_ARTWORK_VERSIONS = ' + json.dumps(versions, ensure_ascii=False, indent=2) + ';\n')
layout_path.write_text(layout[:match.start(1)] + json.dumps(dimensions, ensure_ascii=False, separators=(',',':')) + layout[match.end(1):])
manifest = {'date':'2026-10-11', 'generator':'built-in image_gen', 'installed':len(installed), 'total':144, 'status':'ready-to-publish' if len(installed)==144 else 'in-progress', 'entries':installed}
(ROOT / 'docs/tasks/artwork-style-correction-installed.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'installed':len(installed),'total':144}, ensure_ascii=False))
