#!/usr/bin/env python3
"""Encode reviewed artwork without cropping; preserve paths and update image metadata."""
from pathlib import Path
from PIL import Image
import json, re, hashlib, argparse, subprocess, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(BASE)
parser = argparse.ArgumentParser()
parser.add_argument('manifest')
args = parser.parse_args()
manifest = json.loads(Path(args.manifest).read_text())
progress_path = ROOT / 'docs/tasks/artwork-painterly-progress.json'
progress = json.loads(progress_path.read_text())
versions_path = ROOT / 'app/src/data/schoolArtworkVersions.js'
versions = json.loads(re.search(r'= (\{.*\});', versions_path.read_text(), re.S).group(1))
layout_path = ROOT / 'app/src/data/heroArtworkLayout.js'
layout = layout_path.read_text()
match = re.search(r'const dimensions = (\{[^\n]+\});', layout)
dimensions = json.loads(match.group(1))
results = []
for item in manifest['entries']:
    source = Path(item['source'])
    im = Image.open(source).convert('RGB')
    assert abs(im.width / im.height - 16/9) < .01, (item['name'], im.size)
    source_size = list(im.size)
    target = ROOT / 'app/public' / item['image'].lstrip('/')
    original = subprocess.check_output(['git', 'show', progress['entries'][0]['baselineCommit'] + ':app/public' + item['image']], cwd=ROOT)
    baseline_hash = hashlib.sha256(original).hexdigest()
    # Generation is approximately 16:9; a subpixel ratio adjustment and modest downsample,
    # never crop/paint/outpaint here. All creative edits came from image_gen.
    im = im.resize((1600,900), Image.Resampling.LANCZOS)
    im.save(target, 'WEBP', quality=88, method=6)
    assert Image.open(target).size == (1600,900)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    versions[item['image']] = digest[:12]
    dimensions[item['image']] = [1600,900]
    row = next(r for r in progress['entries'] if r['image'] == item['image'])
    row.update(status='completed-local', generator=manifest['generator'], batch='01',
               sourceImage=str(source), sourceDimensions=source_size, outputDimensions=[1600,900],
               baselineSha256=baseline_hash, newSha256=digest, bytes=target.stat().st_size,
               publication='not-published')
    row['recognitionCue'] = item.get('recognitionCue', row.get('recognitionCue', '已获用户认可的试作主体'))
    row['decision'] = item.get('decision', row.get('decision', 'style-and-reframe'))
    results.append({'name':item['name'],'image':item['image'],'sha256':digest,'source':str(source),'bytes':target.stat().st_size})
versions_path.write_text('// Content hashes for artwork replacements; canonical public paths stay unchanged.\nexport const SCHOOL_ARTWORK_VERSIONS = ' + json.dumps(versions, ensure_ascii=False, indent=2) + ';\n')
layout_path.write_text(layout[:match.start(1)] + json.dumps(dimensions, ensure_ascii=False, separators=(',',':')) + layout[match.end(1):])
progress['completed'] = sum(r['status']=='completed-local' for r in progress['entries'])
progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2))
print(json.dumps({'completed':progress['completed'],'results':results},ensure_ascii=False))
