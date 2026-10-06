"""Frozen record integrity and reporting scope; no model calls or answer reruns."""
import json,shutil,sys
from decimal import Decimal
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import freeze_benchmark_results as seal
from tools import render_benchmark_matrix as view


def record():return json.loads((seal.OUT/'SCORES.json').read_text())

def test_single_cohort_is_explicit_and_identical_for_all_subjects():
 d=record();suite=json.loads((seal.ROOT/'docs/evidence/phiagent_benchmark_v0_1/suite.json').read_text())['cases']
 expected=[c['id'] for c in suite if c['manual_prompt_ready'] and c['rubric_family'] in ['C','R']]
 assert d['primary_case_ids']==expected and len(expected)==60
 assert d['verification_case_ids']==['D01','D02','D04','D05','E05']
 assert d['unrun_fixture_case_ids']==['K01','K02','K03','K04','K05']
 for s in d['subjects']:
  assert s['primary']['case_ids']==sorted(expected) and s['primary']['score'] is not None
  assert sum(r['case_id'] in expected for r in s['rows'])==72


def test_totals_match_independent_decimal_case_then_turn_average():
 d=record();rules=json.loads((seal.ROOT/'docs/evidence/rubric_v1_2/RULES_FROZEN.json').read_text())
 for s in d['subjects']:
  values={cid:[] for cid in d['primary_case_ids']}
  for r in s['rows']:
   if r['case_id'] not in values:continue
   assert 'U' not in r['ratings'].values()
   points=sum(Decimal(rules[k[0]][k]['weight'])*Decimal(v)/4 for k,v in r['ratings'].items())
   values[r['case_id']].append(points*100/(100 if r['family']=='R' else 60))
  total=sum(sum(v)/len(v) for v in values.values())/60
  assert abs(total-Decimal(str(s['primary']['score'])))<Decimal('0.0000000001')


def test_failure_not_excluded_and_unknown_execution_not_imputed():
 d=record();fixed=next(s for s in d['subjects'] if s['id']=='phiagent-0.1.0');item=next(r for r in fixed['verification']['rows'] if r['id']=='D04-T1');assert item['ratings']['K1']==1 and item['score']['exact']['K']==3 and item['source_score_before_adjudication']['exact']['K'] is None
 r=next(s for s in d['subjects'] if s['id']=='phiagent-0.1.2')
 a=next(x for x in r['rows'] if x['id']=='A05-T1');assert set(a['ratings'].values())=={0} and 'A05' in d['primary_case_ids']
 external=next(s for s in d['subjects'] if s['id']=='chatgpt-work-sol61-high-20261002')
 assert external['verification']['complete_cases']==1
 assert all(r['ratings']['K4']=='U' for r in external['verification']['rows'] if r['case_id'] in ['D01','D02','D04','D05'])


def test_visible_matrix_has_one_total_and_no_range_in_primary_rows():
 d=view.matrix();main=d['current']['rows'];assert sum(r['primary'] for r in main)==1
 assert main[0]['label']=='统一60题总分'
 assert all('–' not in v and '待核' not in v for r in main for v in r['values'])
 page=view.html_page(d);assert '<details>' in page and '查看5道原典纯核验' in page
 assert '固定64题子集' not in page and '固定10题指数' not in page


def test_frozen_file_tampering_is_rejected(tmp_path,monkeypatch):
 for p in seal.OUT.iterdir():
  if p.is_file():shutil.copyfile(p,tmp_path/p.name)
 data=json.loads((tmp_path/'SCORES.json').read_text());data['subjects'][0]['primary']['score']+=1
 (tmp_path/'SCORES.json').write_text(json.dumps(data))
 monkeypatch.setattr(seal,'OUT',tmp_path)
 with pytest.raises(AssertionError):seal.verify()
