"""Check current docs naming/links and byte-exact historical moves; no network."""
import json,os,re,sys,urllib.parse
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
DOCS=ROOT/'docs';errors=[];checked=0
for path in DOCS.rglob('*.md'):
 if any(p in path.parts for p in ['archive','evidence']):continue
 if path.name not in ['README.md','分章标准规范.md'] and not re.fullmatch(r'[a-z0-9][a-z0-9.-]*\.md',path.name):errors.append(str(path)+': inconsistent filename')
 text=re.sub(r'```.*?```','',path.read_text(),flags=re.S)
 for m in re.finditer(r'\]\(([^\s)]+)\)',text):
  url=urllib.parse.urlsplit(m[1].strip('<>'))
  if url.scheme or url.netloc or not url.path:continue
  target=(path.parent/urllib.parse.unquote(url.path)).resolve();checked+=1
  if not target.exists():errors.append(str(path.relative_to(ROOT))+': missing '+m[1])
migration=json.loads((DOCS/'reference/docs-migration-2026-10-03.json').read_text())
import hashlib
for item in migration['moves']:
 target=ROOT/item['new']
 if not target.is_file():errors.append('missing moved file '+item['new']);continue
 if '/archive/' in item['new'] and hashlib.sha256(target.read_bytes()).hexdigest()!=item['original_sha256']:errors.append('historical content changed '+item['new'])
if errors:
 print('\n'.join(errors));raise SystemExit(1)
print(json.dumps({'current_local_links_checked':checked,'historical_moves_byte_exact':True,'naming_checked':True,'frozen_evidence_paths_preserved':True,'network_calls':0}))
