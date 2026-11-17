"""November 15 v2 shared parent/review rules and the first three defenses."""
from copy import deepcopy
import json
from pathlib import Path
import runpy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from advocate_bot_qualtrics.practice_areas.consumer_debt.affirmative_defenses import sync_checkbox_parents
from advocate_bot_qualtrics.practice_areas.consumer_debt.session import InteractiveSessionState,apply_interactive_branch
from advocate_bot_qualtrics.practice_areas.consumer_debt.workflow import (
    CONTENT,TREE,DEFENSES,SUMMARY,GuidedEditRequest,edit_review,
)
from advocate_bot_qualtrics.practice_areas.consumer_debt.script_formatting import SOURCE_FORMATTING
from test_november14_revisions import start,reach,step
from test_clickthrough_workflow import answers,intake,review,completed_history

ROOT=Path(__file__).resolve().parents[1]


def test_current_sources_preserve_later_defenses_and_use_v2_for_first_three():
    module=runpy.run_path(str(ROOT/'scripts/extract_script_formatting.py'))
    old=module['extract_formatting'](ROOT/CONTENT['source'])
    revised=module['extract_formatting'](ROOT/CONTENT['revision_source'])
    assert CONTENT['revision_source'].endswith('-v3.docx')
    assert module['extract_prototype_formatting']()==SOURCE_FORMATTING
    def tail(paragraphs):
        i=max(i for i,p in enumerate(paragraphs) if p['text']=='8 Laches')
        return paragraphs[i:]
    assert tail(SOURCE_FORMATTING['paragraphs'])==tail(old['paragraphs'])
    assert SOURCE_FORMATTING['revision_source_sha256']==revised['source_sha256']
    assert SOURCE_FORMATTING['screen_headers']['v3:15']==revised['screen_headers']['15']
    assert SOURCE_FORMATTING['screen_headers']['37']==old['screen_headers']['37']


@pytest.mark.parametrize('creditor',['original','buyer'])
def test_standing_nested_choices_are_independent_and_parent_is_automatic(creditor):
    current=reach(start('standing_privity',guided_creditor_type=creditor),
                  'standing_original_choice' if creditor=='original' else 'standing_first')
    if creditor=='original':
        assert len(TREE.node(current.current).selection_checkboxes)==1
        current=step(current,'yes')
    current=step(current,'yes')
    assert current.session.checkbox_selections['standing_privity']=={'main':'include','first':'include'}
    assert 'provide proof of ownership' in current.page()['title']
    current=step(current,'no')
    assert current.current==DEFENSES['standing_privity']['summary']
    assert current.session.checkbox_selections['standing_privity']=={'main':'include','first':'include','second':'exclude'}
    assert current.page()['rows'][1]['label'].startswith('(1) ')
    assert current.page()['rows'][2]['label'].startswith('(2) ')
    assert 'main ‘Standing/Privity’ checkbox' in current.page()['body'][-1]


def test_original_standing_main_decline_skips_both_arguments_and_has_no_reminder():
    current=reach(start('standing_privity',guided_creditor_type='original'),'standing_original_choice')
    current=step(current,'no')
    assert current.current==DEFENSES['standing_privity']['summary']
    assert current.session.checkbox_selections['standing_privity']=={'main':'exclude'}
    assert current.page()['body']==[CONTENT['confirmation']['empty']]


@pytest.mark.parametrize('node',['standing_original_choice','standing_original_first','standing_original_second'])
def test_standing_uncertainty_does_not_select_the_pending_checkbox(node):
    current=reach(start('standing_privity',guided_creditor_type='original'),node,{'standing_original_choice':'yes','standing_original_first':'no'})
    before=deepcopy(current.session.checkbox_selections)
    current=step(current,'unknown')
    assert current.session.defense_open_questions
    assert current.session.checkbox_selections==before
    current=step(current,'retry')
    assert current.current==node


def test_removing_last_child_clears_derived_parent_and_retains_independent_parent():
    for creditor in ['buyer','original']:
        current=reach(start('standing_privity',guided_creditor_type=creditor),
                      'standing_original_choice' if creditor=='original' else 'standing_first')
        if creditor=='original':current=step(current,'yes')
        first=current.current
        current=step(step(current,'yes'),'no')
        index=next(i for i,a in enumerate(current.history) if a.node_id==first)
        current=edit_review({},GuidedEditRequest(history=current.history,debug_section=current.debug_section,edit_index=index,value='no'))
        assert current.current==DEFENSES['standing_privity']['summary']
        assert current.session.checkbox_selections['standing_privity']['main']==('include' if creditor=='original' else 'exclude')
        assert ('make sure to check off' in ' '.join(current.page()['body']))==(creditor=='original')


def test_main_decline_clears_children_and_later_reselection_does_not_restore_them():
    current=reach(start('standing_privity',guided_creditor_type='original'),'standing_original_choice')
    current=step(step(step(current,'yes'),'yes'),'yes')
    index=next(i for i,a in enumerate(current.history) if a.node_id=='standing_original_choice')
    current=edit_review({},GuidedEditRequest(history=current.history,debug_section=current.debug_section,edit_index=index,value='no'))
    assert current.session.checkbox_selections['standing_privity']=={'main':'exclude'}
    current=edit_review({},GuidedEditRequest(history=current.history,revision=current.revision,debug_section=current.debug_section,edit_index=index,value='yes'))
    assert current.current=='standing_original_first'
    assert current.session.checkbox_selections['standing_privity']=={'main':'include'}


def test_ambiguity_keeps_explanation_and_uses_named_shared_reminder():
    current=reach(start('ambiguity'),'ambiguity_decision')
    assert 'Ambiguity means something is unclear' in ' '.join(current.page()['body'])
    assert step(current,'no').page()['body']==[CONTENT['confirmation']['empty']]
    current=step(current,'yes')
    assert 'main ‘Ambiguity’ checkbox' in current.page()['body'][-1]


def test_sol_has_numbered_labels_and_preserves_explicit_main_selection():
    current=review(completed_history())
    assert [r['label'] for r in current.page()['rows']]==['Statute of Limitations','(1) California written contracts','(2) California oral contracts','(3) Delaware written contracts']
    assert 'main ‘Statute of Limitations’ checkbox' in current.page()['body'][-1]
    current=review(intake('buyer')+answers(('statute_of_limitations_decision','yes'),('sol_checkboxes_first_third','no'),('sol_written','no')))
    assert current.session.checkbox_selections['statute_of_limitations']['main']=='include'


def test_shared_reminder_can_be_customized_per_defense(monkeypatch):
    monkeypatch.setitem(CONTENT['confirmation_reminders'],'ambiguity','Check the “[DEFENSE NAME]” box on Attachment 4, too.')
    current=step(reach(start('ambiguity'),'ambiguity_decision'),'yes')
    assert current.page()['body'][-1]=='Check the “Ambiguity” box on Attachment 4, too.'


def test_parent_graph_maps_all_nested_options_and_has_no_cycles_or_sibling_selection():
    for defense,mapping in CONTENT['checkbox_parents'].items():
        boxes={b.checkbox_id for n in TREE.nodes for b in n.selection_checkboxes if b.defense_id==defense}
        assert set(mapping)<=boxes|{'common_third','breach_parent','common_parent'}
        for child in mapping:
            seen=set();node=child
            while node in mapping:
                assert node not in seen
                seen.add(node);node=mapping[node]
            assert node=='main'
    session=InteractiveSessionState()
    apply_interactive_branch(session,'cause_common_attachment_checkbox','yes',tree=TREE)
    sync_checkbox_parents(session,CONTENT['checkbox_parents'],tree=TREE)
    choices=session.checkbox_selections['failure_to_state_cause']
    assert choices['common_third']==choices['common_parent']==choices['main']=='include'
    assert 'breach_parent' not in choices and 'common_first' not in choices


def test_collection_records_automatic_parent_as_calculation_and_preserves_old_versions(tmp_path):
    from test_research_collection import context,rows
    module=runpy.run_path(str(ROOT/'scripts/run_clickthrough.py'))
    app=module['create_app'](collection_dir=tmp_path)
    sid=uuid4()
    client=TestClient(app)
    # Use a complete ordinary intake path, since collection does not accept debug jumps.
    history=completed_history('buyer')+answers((SUMMARY,'continue'),('ambiguity_decision','no'),(DEFENSES['ambiguity']['summary'],'continue'),('guided_standing_privity_intro','continue'))
    assert review(history).current=='standing_first'
    data={'history':[a.model_dump(mode='json') for a in history]}
    assert client.post('/api/state',json={**data,'session_id':str(sid)}).status_code==200
    response=client.post('/api/advance',json={**data,'value':'yes','collection':context(str(sid))})
    assert response.status_code==200,response.text
    events=[r for r in rows(tmp_path,'responses.csv') if r['RESPONSE.ITEM.ID']=='CHECKBOX.standing_privity.main']
    assert len(events)==1 and events[0]['RESPONSE.ITEM.VALUE']=='include'
    assert events[0]['RESPONSE.EVENT.TYPE']=='Program calculation'
    assert not any(r['RESPONSE.ITEM.ID']=='standing_original_choice' for r in rows(tmp_path,'responses.csv'))
    result=response.json()
    index=next(i for i,a in enumerate(result['history']) if a['node_id']=='standing_first')
    response=client.post('/api/edit',json={'history':result['history'],'revision':result['revision'],
        'edit_index':index,'value':'no','collection':context(str(sid))})
    assert response.status_code==200,response.text
    result=response.json()
    assert result['page']['node_id']=='standing_second_buyer'
    events=[r for r in rows(tmp_path,'responses.csv') if r['RESPONSE.ITEM.ID']=='CHECKBOX.standing_privity.main']
    assert events[-1]['RESPONSE.EVENT.TYPE']=='Program invalidation'
    assert events[-1]['RESPONSE.ITEM.VALUE']==''
    response=client.post('/api/advance',json={'history':result['history'],'revision':result['revision'],
        'value':'no','collection':context(str(sid))})
    assert response.status_code==200,response.text
    events=[r for r in rows(tmp_path,'responses.csv') if r['RESPONSE.ITEM.ID']=='CHECKBOX.standing_privity.main']
    assert [r['RESPONSE.ITEM.VALUE'] for r in events]==['include','','exclude']
    assert events[-1]['RESPONSE.EVENT.TYPE']=='Program calculation'
    original=rows(tmp_path,'sessions.csv')[0]['SESSION.TREE.VERSION']
    historical_events=rows(tmp_path,'responses.csv')
    app.state.collection.version='future-source-fingerprint'
    app.state.collection.start(sid);app.state.collection.start(uuid4())
    assert rows(tmp_path,'sessions.csv')[0]['SESSION.TREE.VERSION']==original
    assert rows(tmp_path,'responses.csv')==historical_events
