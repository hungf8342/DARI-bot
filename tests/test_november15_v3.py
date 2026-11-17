"""V3 accepted sources, first-seven routing, separate reasons, and preserved history."""
from copy import deepcopy
import hashlib,json,runpy
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from advocate_bot_qualtrics.practice_areas.consumer_debt.workflow import (
 CONTENT,TREE,DEFENSES,CONTINUE_PAGES,GuidedEditRequest,edit_review,
)
from advocate_bot_qualtrics.practice_areas.consumer_debt.script_formatting import SOURCE_FORMATTING
from test_november14_revisions import start,step,reach

ROOT=Path(__file__).resolve().parents[1]


def identity(*,recognized='yes',stolen='no',card_choice='no',account_choice='no',recognized_choice='no'):
 current=start('identity_theft',guided_recognize=recognized)
 choices={'identity_stolen_card':stolen,'identity_theft_decision':card_choice,
  'identity_negative_choice':card_choice,'identity_account_choice':account_choice,'identity_recognized_choice':recognized_choice}
 seen=[]
 for _ in range(30):
  seen.append(current.current)
  if current.current==DEFENSES['identity_theft']['summary']:return current,seen
  current=step(current,'continue' if current.current in CONTINUE_PAGES else choices[current.current])
 raise AssertionError('Identity did not complete')


def test_sources_use_v3_through_wrong_party_and_keep_later_paragraphs():
 module=runpy.run_path(str(ROOT/'scripts/extract_script_formatting.py'))
 old=module['extract_formatting'](ROOT/CONTENT['source'])
 revised=module['extract_formatting'](ROOT/CONTENT['revision_source'])
 assert CONTENT['revision_source'].endswith('-v3.docx')
 assert module['extract_prototype_formatting']()==SOURCE_FORMATTING
 def tail(paragraphs):
  start=max(i for i,p in enumerate(paragraphs) if p['text']=='8 Laches')
  return paragraphs[start:]
 assert tail(SOURCE_FORMATTING['paragraphs'])==tail(old['paragraphs'])
 latest=module['extract_formatting'](ROOT/CONTENT['wrong_party_source'])
 assert SOURCE_FORMATTING['screen_headers']['v4:43']==latest['screen_headers']['43']
 assert SOURCE_FORMATTING['screen_headers']['37']==old['screen_headers']['37']
 assert SOURCE_FORMATTING['revision_source_sha256']==hashlib.sha256((ROOT/CONTENT['revision_source']).read_bytes()).hexdigest()
 assert all(p.get('internal') for p in SOURCE_FORMATTING['paragraphs'] if p.get('source')==CONTENT['revision_source'] and 249<=p['source_index']<=262)


@pytest.mark.parametrize('stolen',['yes','no'])
@pytest.mark.parametrize('choice',['yes','no'])
def test_identity_recognized_preserves_card_choice_and_finishes_literally(stolen,choice):
 current,seen=identity(stolen=stolen,card_choice=choice)
 assert ('identity_theft_decision' if stolen=='yes' else 'identity_negative_choice') in seen
 assert ('identity_clinic_notice' if stolen=='yes' else 'identity_negative_notice') in seen if choice=='yes' else not any(n in seen for n in ['identity_clinic_notice','identity_negative_notice'])
 assert 'identity_recognized_choice' in seen
 assert 'identity_finish_recognized' not in seen
 assert current.session.checkbox_selections['identity_theft']['main']==('include' if choice=='yes' else 'exclude')
 assert current.session.defense_results.get('identity_theft',{}).get('status')!='finished'


@pytest.mark.parametrize('first,second',[('yes','no'),('no','yes'),('no','no'),('yes','yes')])
def test_unrecognized_identity_records_both_choices_and_combines_either_yes(first,second):
 current,seen=identity(recognized='no',card_choice=first,account_choice=second)
 assert 'identity_account_choice' in seen
 assert current.session.defense_answers['identity_negative_choice']==first
 assert current.session.defense_answers['identity_account_choice']==second
 assert current.session.checkbox_selections['identity_theft']['main']==('include' if 'yes' in [first,second] else 'exclude')
 reasons=current.page()['rows'][0]['choice_reasons']
 assert len(reasons)==2 and all(r['edit_index'] is not None for r in reasons)
 assert ('identity_account_notice' in seen)==('yes' in [first,second])


@pytest.mark.parametrize('recognized',['yes','no'])
@pytest.mark.parametrize('first,second',[('yes','no'),('no','yes'),('no','no'),('yes','yes')])
def test_wrong_party_asks_both_grounds_and_combines_either_yes(recognized,first,second):
 current,_=identity(recognized=recognized,card_choice='yes',account_choice='no')
 current=step(step(current,'continue'),'continue')
 assert current.current=='wrong_party_identity_choice'
 current=step(current,first)
 if first=='yes':
  assert current.current==DEFENSES['wrong_party']['summary']
  assert current.session.defense_results['wrong_party']['status']=='finished'
  assert current.session.checkbox_selections['wrong_party']['main']=='include'
  assert len(current.page()['rows'][0]['choice_reasons'])==1
  return
 assert current.current==('wrong_party_recognized_choice' if recognized=='yes' else 'wrong_party_account_choice')
 assert current.page()['title']=='Do you want to raise a Wrong Party defense?'
 current=step(current,second)
 if 'yes' in [first,second]:
  assert current.current==('wrong_party_recognized_notice' if recognized=='yes' else 'wrong_party_clinic_notice')
  current=step(current)
 assert current.current==DEFENSES['wrong_party']['summary']
 assert current.session.checkbox_selections['wrong_party']['main']==('include' if 'yes' in [first,second] else 'exclude')
 assert len(current.page()['rows'][0]['choice_reasons'])==2


@pytest.mark.parametrize('recognized',['yes','no'])
def test_wrong_party_without_identity_still_offers_recognition_choice(recognized):
 current=start('wrong_party',guided_recognize=recognized)
 current=step(current)
 assert current.current==('wrong_party_recognized_choice' if recognized=='yes' else 'wrong_party_account_choice')
 current=step(current,'no')
 assert current.current==DEFENSES['wrong_party']['summary']
 assert current.session.checkbox_selections['wrong_party']=={'main':'exclude'}


def test_identity_edit_removes_only_its_ground_and_retains_the_other_explicit_choice():
 current,_=identity(recognized='no',card_choice='yes',account_choice='no')
 index=next(i for i,a in enumerate(current.history) if a.node_id=='identity_negative_choice')
 current=edit_review({},GuidedEditRequest(history=current.history,debug_section=current.debug_section,edit_index=index,value='no'))
 assert current.current==DEFENSES['identity_theft']['summary']
 assert current.session.defense_answers['identity_account_choice']=='no'
 assert current.session.checkbox_selections['identity_theft']['main']=='exclude'
 assert 'confirmation_reminder' not in current.page()


@pytest.mark.parametrize('node',['identity_stolen_card','identity_negative_choice','identity_account_choice','wrong_party_recognized_choice'])
def test_unknown_choices_require_clarification_and_draft_previews_do_not_advance(node):
 current=reach(start('identity_theft' if node.startswith('identity') else 'wrong_party',guided_recognize='no' if node=='identity_account_choice' else 'yes'),node)
 before=deepcopy(current.__dict__)
 current.page();current.preview_response('yes')
 assert current.__dict__==before
 current=step(current,'unknown')
 assert current.session.defense_open_questions
 current=step(current,'retry')
 assert current.current==node


def test_cause_uses_substantive_headers_and_skips_old_parent_pages():
 current=start('failure_to_state_cause',guided_suit_type='both',guided_original_creditor='missing',guided_statement='no',guided_ownership_proof='no')
 seen=[]
 for _ in range(70):
  seen.append(current.current)
  if current.current==DEFENSES['failure_to_state_cause']['summary']:break
  if TREE.node_map.get(current.current) and TREE.node(current.current).selection_checkboxes:
   assert 'Do you want to argue' in current.page()['title']
   assert 'indented checkbox' not in ' '.join(current.page()['body'])
  current=step(current,'continue' if current.current in CONTINUE_PAGES else 'yes')
 else:pytest.fail('Cause did not complete')
 assert 'cause_breach_parent_result' not in seen and 'cause_common_parent_result' not in seen
 assert current.session.checkbox_selections['failure_to_state_cause']['main']=='include'


def test_research_records_independent_choices_and_the_combined_result(tmp_path):
 from test_research_collection import context,rows
 module=runpy.run_path(str(ROOT/'scripts/run_clickthrough.py'))
 client=TestClient(module['create_app'](collection_dir=tmp_path))
 from test_guided_november_scripts import reach as normal_reach
 current=normal_reach('identity_theft',recognize='no')
 current=step(step(step(current,'no'),'yes'))
 assert current.current=='identity_account_choice'
 prefix=[a.model_dump(mode='json') for a in current.history]
 sid=str(uuid4())
 assert client.post('/api/state',json={'history':prefix,'session_id':sid}).status_code==200
 response=client.post('/api/advance',json={'history':prefix,'value':'no','collection':context(sid)})
 assert response.status_code==200,response.text
 events=rows(tmp_path,'responses.csv')
 assert next(r for r in events if r['RESPONSE.ITEM.ID']=='identity_account_choice')['RESPONSE.ITEM.VALUE']=='no'
 assert next(r for r in events if r['RESPONSE.ITEM.ID']=='CHECKBOX.identity_theft.main')['RESPONSE.ITEM.VALUE']=='include'
 assert rows(tmp_path,'defenses.csv')[0]['DEFENSE.identity_theft.CHECKED']=='Yes'
 old_events=deepcopy(events);old_version=rows(tmp_path,'sessions.csv')[0]['SESSION.TREE.VERSION']
 app=module['create_app'](collection_dir=tmp_path)
 app.state.collection.version='future-source';app.state.collection.start(__import__('uuid').UUID(sid))
 assert rows(tmp_path,'responses.csv')==old_events
 assert rows(tmp_path,'sessions.csv')[0]['SESSION.TREE.VERSION']==old_version
