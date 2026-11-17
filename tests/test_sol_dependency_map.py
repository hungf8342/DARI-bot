"""SOL dependencies preserve explicit main inclusion before nested choices."""
from itertools import product
import pytest

from advocate_bot_qualtrics.practice_areas.consumer_debt.sol_dependency_map import (
    affected_checkboxes, load_dependency_map, plan_checkbox_review,
)
from advocate_bot_qualtrics.practice_areas.consumer_debt.workflow import TREE

QUESTIONS={'plaintiff_type':'sol_creditor_type_resolve','payment_timing':'sol_payment_age','oral_agreement':'sol_oral_gate_resolve'}


def plan(creditor,timing,oral,choices=None):
    return plan_checkbox_review({'plaintiff_type':creditor,'payment_timing':timing,'oral_agreement':oral},QUESTIONS,choices or {})


@pytest.mark.parametrize('timing',[None,'qualifying','recent','uncertain'])
def test_debt_buyer_needs_no_timing_before_main_choice(timing):
    result=plan('buyer',timing,None)
    assert result.availability=={'main':True,'first':None,'third':None,'second':None}
    assert result.required_questions==['statute_of_limitations_decision']
    assert result.used_facts==['plaintiff_type']


def test_unknown_creditor_is_resolved_before_any_selection():
    result=plan(None,None,None)
    assert all(v is None for v in result.availability.values())
    assert result.required_questions==['sol_creditor_type_resolve']


@pytest.mark.parametrize('timing',['qualifying','recent','uncertain'])
def test_each_original_creditor_result_offers_main_but_does_not_infer_inclusion(timing):
    result=plan('original',timing,None)
    assert result.availability=={'main':True,'first':None,'third':None,'second':None}
    assert result.required_questions==['statute_of_limitations_decision']
    assert result.used_facts==['plaintiff_type','payment_timing']


@pytest.mark.parametrize('oral',['yes','no',None])
def test_declining_main_skips_nested_and_oral_questions(oral):
    result=plan('buyer',None,oral,{'main':'no'})
    assert result.availability=={'main':True,'first':False,'third':False,'second':False}
    assert result.required_questions==[]
    assert 'oral_agreement' not in result.used_facts


@pytest.mark.parametrize('oral,node',[('yes','sol_checkbox_second'),('no','sol_written')])
def test_both_contract_types_need_a_second_reason_choice_after_main_inclusion(oral,node):
    result=plan('buyer',None,oral,{'main':'yes'})
    assert all(result.availability.values())
    assert result.required_questions==['sol_checkboxes_first_third',node]


def test_unknown_contract_type_is_requested_only_after_main_inclusion():
    result=plan('buyer',None,None,{'main':'yes','first':'no','third':'no'})
    assert result.required_questions==['sol_oral_gate_resolve']
    assert result.availability['second'] is None


def test_saved_choices_do_not_override_unknown_original_creditor_timing():
    result=plan('original',None,'yes',{'main':'yes','first':'yes','third':'yes','second':'yes'})
    assert result.required_questions==['sol_payment_age']
    assert all(value is None for value in result.availability.values())


@pytest.mark.parametrize('field,expected',[
 ('guided_plaintiff',set()),('guided_original_creditor',set()),
 ('guided_oral',{'second'}),('guided_creditor_type',{'main','first','third','second'}),
 ('guided_payment_date',{'main','first','third','second'}),('guided_filing_date',{'main','first','third','second'}),
 ('statute_of_limitations_decision',{'main','first','third','second'}),
 ('sol_checkboxes_first_third',{'first','third'}),('sol_written',{'second'}),
])
def test_backward_edges_include_main_selection_and_both_oral_choice_screens(field,expected):
    assert set(affected_checkboxes(field))==expected


def test_dependency_questions_match_current_checkbox_metadata():
    data=load_dependency_map()
    for box,spec in data['checkboxes'].items():
        for question in [spec['question'],*spec.get('alternate_questions',[])]:
            assert box in {b.checkbox_id for b in TREE.node(question).selection_checkboxes}
    for fact in data['facts'].values():
        for question in fact['questions']:assert TREE.node(question).kind=='choice'


@pytest.mark.parametrize('creditor,timing,oral,main',list(product(['original','buyer'],['qualifying','recent','uncertain'],['yes','no'],['yes','no'])))
def test_planner_and_actual_traversal_agree_on_offered_boxes(creditor,timing,oral,main):
    from test_clickthrough_workflow import intake,review,answers
    from advocate_bot_qualtrics.practice_areas.consumer_debt.workflow import SUMMARY
    history=intake(creditor,payment='missing',oral=oral)
    current=review(history);offered=set()
    for _ in range(20):
        if current.current==SUMMARY:break
        node=TREE.node(current.current)
        if node.selection_checkboxes:
            offered.update(b.checkbox_id for b in node.selection_checkboxes)
            value=main if node.id=='statute_of_limitations_decision' else 'no'
        elif node.id=='sol_payment_age':value={'qualifying':'no','recent':'yes','uncertain':'unknown'}[timing]
        else:pytest.fail(node.id)
        history+=answers((node.id,value));current=review(history)
    else:pytest.fail('SOL failed to reach review')
    expected=plan(creditor,timing,oral,{'main':main})
    assert offered=={box for box,available in expected.availability.items() if available}
