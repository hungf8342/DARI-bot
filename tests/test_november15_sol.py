"""November 15 SOL-only wording, explicit choices, editing, and source isolation."""
import hashlib
import json
from pathlib import Path
import runpy

import pytest
from fastapi.testclient import TestClient

from advocate_bot_qualtrics.practice_areas.consumer_debt.workflow import (
    CONTENT, CONTINUE_PAGES, DEFENSE, SUMMARY, TREE, ClickthroughReview,
    GuidedAdvanceRequest, GuidedEditRequest, advance_review, edit_review,
)
from advocate_bot_qualtrics.practice_areas.consumer_debt.script_formatting import SOURCE_FORMATTING
from test_clickthrough_workflow import intake, review, answers

ROOT=Path(__file__).resolve().parents[1]


def step(current,value):
    return advance_review(current.defaults,GuidedAdvanceRequest(history=current.history,revision=current.revision,
        debug_section=current.debug_section,value=value))


def main_choice(creditor='original',payment='2024-03-15',oral='no',timing=None):
    current=review(intake(creditor,payment=payment,oral=oral))
    if creditor=='original':
        current=step(current,timing if payment=='missing' else 'yes')
    assert current.current=='statute_of_limitations_decision'
    return current


def complete_sol(creditor='original',payment='2024-03-15',oral='no',main='yes',group='yes',second='no',timing=None):
    current=step(main_choice(creditor,payment,oral,timing),main)
    if main=='yes':
        current=step(current,group)
        current=step(current,second)
    assert current.current==SUMMARY
    return current


def section_bounds(paragraphs):
    start=max(i for i,p in enumerate(paragraphs) if p['text']=='1 Statute of Limitations')
    end=next(i for i in range(start+1,len(paragraphs)) if paragraphs[i]['text']=='2 Ambiguity')
    return start,end


def test_sol_uses_the_current_november15_v2_source():
    module=runpy.run_path(str(ROOT/'scripts/extract_script_formatting.py'))
    assert CONTENT['sol_source'].endswith('-v3.docx')
    assert module['extract_prototype_formatting']()==SOURCE_FORMATTING
    assert hashlib.sha256((ROOT/CONTENT['sol_source']).read_bytes()).hexdigest()==SOURCE_FORMATTING['sol_source_sha256']


def test_other_fourteen_defenses_retain_their_november14_nodes_and_routes():
    labels={'Statute of Limitations', 'Identity Theft', 'Standing and Privity', 'Wrong Party', 'Mistake', 'Failure to State a Cause of Action', 'Ambiguity'}
    nodes=[n.model_dump() for n in TREE.nodes if n.discussion_topic not in labels]
    digest=hashlib.sha256(json.dumps(nodes,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    assert digest=='9b64a706b4f3f6afc110011cc9b75bd3cebee40479ecb946c0c9b8893da9de8c'


@pytest.mark.parametrize('payment,timing',[('2024-03-15',None),('2026-07-01',None),('missing','unknown')])
def test_every_resolved_original_creditor_timing_path_gets_an_explicit_main_choice(payment,timing):
    current=main_choice(payment=payment,timing=timing)
    assert not current.session.checkbox_selections
    body=' '.join(current.page()['body'])
    if payment=='2026-07-01':assert 'often skip this defense' in body
    else:assert 'often raise this defense' in body
    if timing=='unknown':
        assert 'not sure whether' in body
        assert 'You said your last payment was on or before' not in body
        assert current.session.defense_answers['sol_payment_age']=='unknown'
    elif payment=='2024-03-15':
        assert 'You said your last payment was on or before' in body
        assert 'not sure whether' not in body
    assert step(current,'no').current==SUMMARY


@pytest.mark.parametrize('creditor',['original','buyer'])
@pytest.mark.parametrize('oral',['yes','no','unknown'])
def test_declining_main_skips_every_nested_choice_even_with_unresolved_oral_status(creditor,oral):
    current=step(main_choice(creditor,oral=oral),'no')
    assert current.current==SUMMARY
    assert current.session.checkbox_selections[DEFENSE]=={'main':'exclude'}
    assert not any(a.node_id in {'sol_checkboxes_first_third','sol_checkbox_second','sol_written','sol_oral_gate_resolve'} for a in current.history)
    assert all(r['status']=='Not offered on this path' for r in current.page()['rows'] if r['id']!='main')


@pytest.mark.parametrize('oral,node,phrase',[('yes','sol_checkbox_second','You said your contract'),('no','sol_written','People in this situation often skip')])
@pytest.mark.parametrize('choice',['yes','no'])
def test_oral_and_written_paths_both_record_the_user_choice(oral,node,phrase,choice):
    current=step(main_choice('buyer',oral=oral),'yes')
    assert 'California and Delaware written contracts' in current.page()['title']
    assert all('box' not in option['label'] for option in current.page()['options'])
    current=step(current,'no')
    assert current.current==node and current.current not in CONTINUE_PAGES
    assert current.page()['input_type']=='choice'
    assert phrase in ' '.join(current.page()['body'])
    assert current.page()['question_text']=='Do you want to raise a Statute of Limitations defense for oral contracts?'
    current=step(current,choice)
    assert current.current==SUMMARY
    assert current.session.checkbox_selections[DEFENSE]=={'main':'include','first':'exclude','third':'exclude','second':'include' if choice=='yes' else 'exclude'}


def test_written_uncertainty_requires_clarification_then_an_explicit_choice():
    current=step(step(main_choice('buyer'),'yes'),'yes')
    current=step(current,'unknown')
    assert current.current=='sol_written_unresolved_help'
    assert current.session.defense_open_questions
    assert current.session.checkbox_selections[DEFENSE].get('second') is None
    current=step(current,'continue')
    assert current.current=='sol_written'
    current=step(current,'no')
    assert not current.session.defense_open_questions
    assert current.session.checkbox_selections[DEFENSE]['second']=='exclude'


def test_old_written_continue_answer_cannot_silently_become_a_selection():
    current=step(step(main_choice('buyer'),'yes'),'yes')
    with pytest.raises(ValueError,match='Choose one of the answers'):
        step(current,'continue')


def test_main_edit_discards_nested_choices_and_does_not_resurrect_them():
    current=complete_sol('buyer',oral='yes',second='yes')
    index=next(i for i,a in enumerate(current.history) if a.node_id=='statute_of_limitations_decision')
    current=edit_review({},GuidedEditRequest(history=current.history,edit_index=index,value='no'))
    assert current.current==SUMMARY
    assert current.session.checkbox_selections[DEFENSE]=={'main':'exclude'}
    assert len(current.page()['changes'])==4
    current=edit_review({},GuidedEditRequest(history=current.history,edit_index=index,value='yes',revision=current.revision))
    assert current.current=='sol_checkboxes_first_third'
    assert current.session.checkbox_selections[DEFENSE]=={'main':'include'}


def test_changing_contract_type_asks_the_new_choice_instead_of_reusing_its_old_answer():
    current=complete_sol('buyer',oral='yes',second='yes')
    index=next(i for i,a in enumerate(current.history) if a.node_id=='guided_oral')
    current=edit_review({},GuidedEditRequest(history=current.history,edit_index=index,value='no'))
    assert current.current=='sol_written'
    assert current.session.checkbox_selections[DEFENSE].get('second') is None
    assert step(current,'no').session.checkbox_selections[DEFENSE]['second']=='exclude'


def test_collection_records_recent_main_decline_and_written_choice(tmp_path):
    from uuid import uuid4
    from test_research_collection import context,rows
    module=runpy.run_path(str(ROOT/'scripts/run_clickthrough.py'))
    client=TestClient(module['create_app'](collection_dir=tmp_path))
    current=main_choice(payment='2026-07-01');sid=str(uuid4())
    history=[a.model_dump(mode='json') for a in current.history]
    assert client.post('/api/state',json={'history':history,'session_id':sid}).status_code==200
    response=client.post('/api/advance',json={'history':history,'value':'no','collection':context(sid)})
    assert response.status_code==200
    data=rows(tmp_path,'defenses.csv')[0]
    assert data['DEFENSE.statute_of_limitations.CHECKED']=='No'
    assert data['DEFENSE.statute_of_limitations.TREE.PROJECTION']=='Yes'
    current=step(step(main_choice('buyer'),'yes'),'yes');sid=str(uuid4())
    history=[a.model_dump(mode='json') for a in current.history]
    assert client.post('/api/state',json={'history':history,'session_id':sid}).status_code==200
    response=client.post('/api/advance',json={'history':history,'value':'no','collection':context(sid)})
    assert response.status_code==200
    events=[r for r in rows(tmp_path,'responses.csv') if r['SESSION.ID']==sid and r['RESPONSE.ITEM.ID']=='sol_written']
    assert len(events)==1 and events[0]['RESPONSE.ITEM.VALUE']=='no'
    assert events[0]['RESPONSE.EVENT.TYPE']=='First submission'


def test_sol_source_version_transition_preserves_historical_research(tmp_path):
    from uuid import uuid4
    from advocate_bot_qualtrics.practice_areas.consumer_debt.research_collection import ResearchCollection
    from test_research_collection import rows
    old=ResearchCollection(tmp_path)
    old.version='guided-21-defenses-2026-11-14-historical'
    sid=uuid4();old.start(sid)
    with old.connect() as db:
        data=json.loads(db.execute('SELECT data FROM sessions WHERE id=?',(str(sid),)).fetchone()[0])
        data['values']['sol_written']='continue'
        old.save(db,sid,data)
        db.execute('INSERT INTO responses(session_id,data) VALUES (?,?)',
                   (str(sid),json.dumps({'SESSION.ID':str(sid),'RESPONSE.ITEM.ID':'legacy-sol-answer','RESPONSE.ITEM.VALUE':'yes'})))
    old.refresh()
    historical=rows(tmp_path,'responses.csv')
    current=ResearchCollection(tmp_path)
    current.start(sid)
    new_sid=uuid4();current.start(new_sid)
    sessions={r['SESSION.ID']:r for r in rows(tmp_path,'sessions.csv')}
    assert sessions[str(sid)]['SESSION.TREE.VERSION']==old.version
    assert sessions[str(new_sid)]['SESSION.TREE.VERSION'].startswith('guided-21-defenses-2026-11-14-1-5-v3-shared-identity-wrong-party-v4-')
    assert rows(tmp_path,'responses.csv')==historical
    with current.connect() as db:
        restored=json.loads(db.execute('SELECT data FROM sessions WHERE id=?',(str(sid),)).fetchone()[0])
    assert restored['values']['sol_written']=='continue'
