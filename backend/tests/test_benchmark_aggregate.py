"""Regression tests for suite-level arithmetic, not answer-quality tests."""
import copy
import json
from fractions import Fraction
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import aggregate_benchmark_scores as agg
RULES=json.loads((agg.ROOT/'docs/evidence/rubric_v1_2/RULES_FROZEN.json').read_text())


def row(cid='A01', turn=1, value=4, family='C'):
    keys=RULES['K'] if family=='K' else [*RULES['C'], *RULES['R']] if family=='R' else RULES['C']
    return {'id':f'{cid}-T{turn}','case_id':cid,'family':family,
            'ratings':dict.fromkeys(keys,value),'question':str(turn),'review_level':'Codex targeted review'}


def case(cid='A01', turns=1, family='C'):
    return {'id':cid,'prompt':'1','follow_up_turns':[str(i) for i in range(2,turns+1)],'rubric_family':family}


def test_each_family_keeps_frozen_internal_weights():
    assert agg.turn_bounds(row(),RULES)==(100,100)
    assert agg.turn_bounds(row(value=2),RULES)==(50,50)
    assert agg.turn_bounds(row(value=3,family='R'),RULES)==(75,75)
    r=row(value=1,family='K');r['ratings']['K1']=0
    assert agg.turn_bounds(r,RULES)==(75,75)
    r=row();r['ratings']['C3']=0
    assert agg.turn_bounds(r,RULES)==(Fraction(200,3),Fraction(200,3))


def test_unknown_dimension_is_an_interval_without_altering_rating():
    r=row(family='K',value=1);r['ratings']['K1']='U';before=copy.deepcopy(r)
    assert agg.turn_bounds(r,RULES)==(75,100)
    assert r==before
    assert agg.export(agg.turn_bounds(r,RULES))['score'] is None


def test_multiturn_case_does_not_get_triple_weight():
    rows=[row('A01',1,0),*[row('J01',i,4) for i in [1,2,3]]]
    result=agg.summarize(rows,[case(),case('J01',3)],RULES)
    assert agg.cohort(result,{'A01','J01'})['score']==50


def test_missing_turn_not_silently_dropped():
    result=agg.summarize([row('J01',1,4)],[case('J01',2)],RULES)
    assert result['J01']['bounds']==(50,100)
    assert not result['J01']['complete']


def test_unrun_case_neither_zero_nor_full_score():
    result=agg.summarize([row()],[case(),case('K01')],RULES)
    assert result['K01']['bounds']==(0,100)
    assert agg.cohort(result,set(result))['score'] is None
    assert agg.cohort(result,set(result))['lower']==50
    assert agg.cohort(result,{'A01'})['score']==100


@pytest.mark.parametrize('value',[True,2.5,-1,5,None])
def test_wrong_scale_is_rejected(value):
    with pytest.raises(ValueError):agg.turn_bounds(row(value=value),RULES)


def test_k_wrong_scale_not_rescaled():
    with pytest.raises(ValueError):agg.turn_bounds(row(value=4,family='K'),RULES)


def test_changed_question_duplicate_or_wrong_family_is_rejected():
    with pytest.raises(ValueError):agg.summarize([row(),row()],[case()],RULES)
    r=row();r['question']='different'
    with pytest.raises(ValueError):agg.summarize([r],[case()],RULES)
    with pytest.raises(ValueError):agg.summarize([row(family='R')],[case()],RULES)


def test_no_unknown_or_partial_cohort_is_promoted_to_full_benchmark():
    data=agg.build()
    assert data['no_quality_pass_claim']
    for version in ['0.1.0','0.1.1']:
        assert data['runs'][version]['full_frozen_suite']['score'] is None
        assert data['runs'][version]['common_fully_scored_cases']['case_count']==64
    assert data['runs']['0.2.0']['score'] is None
