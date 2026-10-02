"""Check the canonical PhiAgent manifest before building/tagging a release."""
import hashlib
import json
import os
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT=BASE.parent


def check():
    release=json.loads((BASE/'agent_release.json').read_text())
    package=json.loads((ROOT/'agent-app/package.json').read_text())
    errors=[]
    if release['release_version']!=package['version']:errors.append('frontend package version differs from canonical release')
    lock=ROOT/'agent-app/package-lock.json'
    if lock.is_file():
        value=json.loads(lock.read_text())
        if value.get('version')!=release['release_version'] or value.get('packages',{}).get('',{}).get('version')!=release['release_version']:
            errors.append('frontend lock version differs from canonical release')
    if release['active_prompt_version'] not in release['prompts']:errors.append('unregistered active prompt')
    for version,item in release['prompts'].items():
        path=BASE/item['path']
        if not path.is_file():errors.append(f'{version}: prompt file missing');continue
        text=path.read_text().rstrip('\n')
        if hashlib.sha256(text.encode()).hexdigest()!=item['sha256']:errors.append(f'{version}: prompt differs from registered fingerprint')
    for path in release['runtime_sources']:
        if not (BASE/path).is_file():errors.append(f'runtime module missing: {path}')
    if release['tool_budget'] is not None:errors.append('this release must not install a tool budget')
    return {'ok':not errors,'release_version':release['release_version'],'errors':errors}


if __name__=='__main__':
    result=check();print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['ok'] else 1)
