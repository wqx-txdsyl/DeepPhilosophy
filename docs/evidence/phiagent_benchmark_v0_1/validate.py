"""Validate test-set structure and delivery integrity, not agent performance."""
import hashlib
import json
from collections import Counter
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[2]
suite = json.loads((base / 'suite.json').read_text())
cases = suite['cases']
prompts = [json.loads(line) for line in (base / 'prompts.jsonl').read_text().splitlines()]
coverage = json.loads((base / 'coverage.json').read_text())
fixtures = json.loads((base / 'fixtures.json').read_text())['fixtures']
expected = {f'{group}{number:02d}' for group in 'ABCDEFGHIJKLMN' for number in range(1, 6)}
assert len(cases) == 70 and {c['id'] for c in cases} == expected
assert len(prompts) == 70 and {p['id'] for p in prompts} == expected
assert suite['metadata']['case_count'] == 70
assert len(suite['metadata']['categories']) == 14
assert dict(Counter(c['category'] for c in cases)) == coverage['by_category']
assert dict(Counter(c['rubric_family'] for c in cases)) == coverage['by_family']
assert dict(Counter(c['tool_expectation']['web'] for c in cases)) == coverage['web_policy']
assert sum(c['manual_prompt_ready'] for c in cases) == coverage['manual_prompt_ready'] == 65
assert sum(c['fixture'] is not None for c in cases) == coverage['fixture_design_only'] == 5
assert {c['fixture'] for c in cases if c['fixture']} == set(fixtures)
assert coverage['runs_completed'] == suite['metadata']['live_agent_runs'] == 0
assert suite['metadata']['is_holdout'] is False
assert suite['metadata']['rubric_changes'] is False
by_id = {c['id']: c for c in cases}
for prompt in prompts:
    case = by_id[prompt['id']]
    assert prompt['messages'] == [{'role': 'user', 'content': case['prompt']}]
    assert prompt['follow_up_turns'] == case['follow_up_turns']
    assert prompt['fixture_id'] == case['fixture']
    assert prompt['manual_prompt_ready'] == case['manual_prompt_ready']
    assert not {'required_work', 'failure_signals', 'philosophical_work', 'rubric_family'} & prompt.keys()
for case in cases:
    assert case['rubric_family'] in {'C', 'R', 'K'}
    assert all(v in suite['metadata']['tool_policy_values'] for v in case['tool_expectation'].values())
    assert len(case['required_work']) == len(case['failure_signals']) == 3
    assert case['reference_pack_status'] == 'not_yet_independently_verified'
    assert case['execution_status'] == 'not_run'
    assert case['automated_harness_ready'] is False
    assert all(isinstance(t, str) and t.strip() for t in case['follow_up_turns'])
doc = (root / 'docs/evidence/PHIAGENT_BENCHMARK_V0_1.md').read_text()
assert all(f'**{c["id"]}｜{c["prompt"]}**' in doc for c in cases)
manifest_path = base / 'MANIFEST.json'
integrity = None
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    integrity = all(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
                    for name, digest in manifest['files'].items())
    assert integrity, 'delivery manifest does not match'
print(json.dumps({'structure_valid': True, 'cases': len(cases), 'categories': 14,
                  'manual_prompt_ready': 65, 'fixture_design_only': 5,
                  'prompt_export_matches': True, 'manifest_integrity': integrity,
                  'agent_runs': 0, 'benchmark_validity_established': False}, ensure_ascii=False, indent=2))
