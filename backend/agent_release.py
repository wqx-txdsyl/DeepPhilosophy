"""One release manifest for general-agent prompt, contracts and run provenance.

Historical prompts are explicit comparison profiles. Credentials are never part
of a descriptor; hashes cover only declared public code/data artifacts.
"""
import hashlib
import json
import os
import subprocess
import importlib.metadata
from pathlib import Path

BASE=Path(__file__).resolve().parent
MANIFEST=json.loads((BASE/'agent_release.json').read_text())
VERSION=MANIFEST['release_version']


def prompt_spec(language='zh', profile=None):
    version=profile or os.environ.get('PHIAGENT_PROMPT_VERSION') or MANIFEST['active_prompt_version']
    if version not in MANIFEST['prompts']:
        raise ValueError('Unknown PHIAGENT_PROMPT_VERSION; choose a registered manifest profile')
    item=MANIFEST['prompts'][version]
    template=(BASE/item['path']).read_text().rstrip('\n')
    locale=('Answer and reason in English; clearly distinguish original quotations from your translations.' if language=='en'
            else '使用中文回答和思考；引用外文时区分原文与译文，不把自译当作来源原文。')
    text=template+'\n\n'+locale
    return {'text':text,'version':version,'template_sha256':hashlib.sha256(template.encode()).hexdigest(),
            'effective_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'manifest_hash_matches':hashlib.sha256(template.encode()).hexdigest()==item['sha256']}


def fingerprint(metadata):
    metadata={k:v for k,v in metadata.items() if k!='configuration_fingerprint'}
    return hashlib.sha256(json.dumps(metadata,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def release_descriptor(language='zh', profile=None):
    prompt=prompt_spec(language,profile)
    sources={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in MANIFEST['runtime_sources']}
    catalogue=BASE.parent/'app/public/books.json'
    try:
        git=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True,stderr=subprocess.DEVNULL).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain','--',*['backend/'+s for s in MANIFEST['runtime_sources']],
                      'backend/agent_release.json','backend/prompts'],cwd=BASE.parent,text=True,stderr=subprocess.DEVNULL).strip())
    except (OSError,subprocess.CalledProcessError):git=None;dirty=None
    dependencies={}
    for name in ('openai','langchain-core','langchain-deepseek','langgraph','httpx','httpx2','httpcore2'):
        try:dependencies[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:dependencies[name]=None
    metadata={'release_version':VERSION,'prompt_version':prompt['version'],'prompt_template_sha256':prompt['template_sha256'],
        'effective_prompt_sha256':prompt['effective_sha256'],'prompt_matches_manifest':prompt['manifest_hash_matches'],
        'tool_contract_version':MANIFEST['tool_contract_version'],'runtime_profile':os.environ.get('DEEP_AGENT_RUNTIME','bare'),
        'model':os.environ.get('DEEP_MAIN_MODEL') or os.environ.get('AGENT_MODEL') or MANIFEST['model_default'],
        'reasoning_effort':os.environ.get('DEEP_AGENT_REASONING_EFFORT','high'),
        'scholarly_network_mode':os.environ.get('SCHOLARLY_NETWORK_MODE','AUTO'),
        'research_db_enabled':os.environ.get('PHI_RESEARCH_DB_ENABLED','').lower() in {'1','true','yes'},
        'data_schemas':MANIFEST.get('data_schemas',{}),
        'dependencies':dependencies,
        'tool_budget':None if os.environ.get('DEEP_AGENT_RUNTIME','bare')=='bare' else 'legacy_controlled_runtime',
        'rubric_version':MANIFEST['rubric_version'],'benchmark_suite_version':MANIFEST['benchmark_suite_version'],
        'git_commit':git,'tracked_runtime_dirty':dirty,'runtime_source_sha256':sources,
        'catalogue_sha256':hashlib.sha256(catalogue.read_bytes()).hexdigest() if catalogue.is_file() else None,
        'status':MANIFEST['status'],'legacy_prompt_selector':os.environ.get('DEEP_PROMPT_VERSION'),
        'legacy_selector_used_by_bare':False,
        'historical_prompt_override':prompt['version']!=MANIFEST['active_prompt_version']}
    metadata['configuration_fingerprint']=fingerprint(metadata)
    return metadata
