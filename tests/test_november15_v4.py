"""V4 recognized-account choices, Wrong Party early finish, and mixed sources."""
import hashlib,json,runpy
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from advocate_bot_qualtrics.practice_areas.consumer_debt.workflow import (
 CONTENT,TREE,DEFENSES,GuidedEditRequest,edit_review,
)
from advocate_bot_qualtrics.practice_areas.consumer_debt.script_formatting import SOURCE_FORMATTING
from test_november15_v3 import identity
from test_november14_revisions import start,step,reach

ROOT=Path(__file__).resolve().parents[1]


def test_v4_scope_and_provenance_preserve_the_earlier_source_sections():
 module=runpy.run_path(str(ROOT/'scripts/extract_script_formatting.py'))
 v3=module['extract_formatting'](ROOT/CONTENT['revision_source'])
 v4=module['extract_formatting'](ROOT/CONTENT['shared_source'])
 assert CONTENT['sol_source'].endswith('-v3.docx')
 assert CONTENT['identity_source']==CONTENT['wrong_party_source']==CONTENT['shared_source']
 assert CONTENT['shared_source'].endswith('-v4.docx')
 assert module['extract_prototype_formatting']()==SOURCE_FORMATTING
 for source,key in [(v3,'revision_source'),(v4,'shared_source')]:
  assert source['source_sha256']==SOURCE_FORMATTING[key+'_sha256']
 for paragraph in SOURCE_FORMATTING['paragraphs']:
  if paragraph.get('source')==CONTENT['revision_source']:
   assert 76<=paragraph['source_index']<423
  elif paragraph.get('source')==CONTENT['shared_source']:
   assert paragraph['source_index']<76 or 423<=paragraph['source_index']<505
 assert SOURCE_FORMATTING['screen_headers']['v4:38']=='Do you want to raise an Identity Theft defense?'
 assert SOURCE_FORMATTING['screen_headers']['v4:43']=='Do you want to raise a Wrong Party defense?'


@pytest.mark.parametrize('stolen',['yes','no'])
@pytest.mark.parametrize('card,recognized',[('yes','yes'),('yes','no'),('no','yes'),('no','no')])
def test_recognized_accounts_get_an_explicit_choice_and_keep_either_yes(stolen,card,recognized):
 current,seen=identity(stolen=stolen,card_choice=card,recognized_choice=recognized)
 assert 'identity_recognized_choice' in seen
 assert 'identity_finish_recognized' not in seen
 assert current.session.defense_answers['identity_recognized_choice']==recognized
 selected='yes' in [card,recognized]
 assert current.session.checkbox_selections['identity_theft']['main']==('include' if selected else 'exclude')
 assert ('identity_recognized_notice' in seen)==selected
 assert len(current.page()['rows'][0]['choice_reasons'])==2
 assert ('confirmation_reminder' in current.page())==selected


@pytest.mark.parametrize('recognized',['yes','no'])
def test_wrong_party_acceptance_on_identity_path_finishes_immediately(recognized):
 current,_=identity(recognized=recognized,card_choice='yes')
 current=step(step(current))
 assert current.current=='wrong_party_identity_choice'
 current=step(current,'yes')
 assert current.current==DEFENSES['wrong_party']['summary']
 assert current.session.defense_results['wrong_party']['status']=='finished'
 assert current.session.checkbox_selections['wrong_party']['main']=='include'
 assert not any(a.node_id in ['wrong_party_account_choice','wrong_party_recognized_choice'] for a in current.history)
 assert 'Wrong Party' in current.page()['confirmation_reminder']


def test_editing_the_recognized_choice_retains_an_independent_stolen_card_selection():
 current,_=identity(card_choice='yes',recognized_choice='yes')
 index=next(i for i,a in enumerate(current.history) if a.node_id=='identity_recognized_choice')
 current=edit_review({},GuidedEditRequest(history=current.history,debug_section=current.debug_section,edit_index=index,value='no'))
 assert current.session.checkbox_selections['identity_theft']['main']=='include'
 assert current.session.defense_answers['identity_negative_choice']=='yes'


def test_editing_wrong_party_early_finish_opens_a_new_recognition_choice():
 current,_=identity(card_choice='yes')
 current=step(step(current));current=step(current,'yes')
 index=next(i for i,a in enumerate(current.history) if a.node_id=='wrong_party_identity_choice')
 current=edit_review({},GuidedEditRequest(history=current.history,debug_section=current.debug_section,edit_index=index,value='no'))
 assert current.current=='wrong_party_recognized_choice'
 assert current.session.defense_answers.get('wrong_party_recognized_choice') is None


def test_recognized_choice_uncertainty_requires_clarification_and_does_not_invent_yes():
 current=reach(start('identity_theft',guided_recognize='yes'),'identity_recognized_choice')
 assert current.session.checkbox_selections['identity_theft']['main']=='exclude'
 current=step(current,'unknown')
 assert current.session.defense_open_questions
 assert current.session.checkbox_selections['identity_theft'].get('main') is None
 assert step(current,'retry').current=='identity_recognized_choice'


def test_unknown_recognition_returns_to_intake_without_treating_it_as_no():
 current=reach(start('identity_theft',guided_recognize='unknown'),'identity_negative_choice')
 current=step(current,'no')
 assert current.current=='guided_recognize'
 current=step(current,'unknown')
 assert current.current=='guided_recognize'
 current=step(current,'yes')
 assert current.current=='identity_recognized_choice'


def test_debug_mode_runs_v4_without_creating_research_records(tmp_path):
 module=runpy.run_path(str(ROOT/'scripts/run_clickthrough.py'))
 directory=tmp_path/'collection'
 app=module['create_app'](debug=True,collection_dir=directory)
 client=TestClient(app)
 assert 'data-debug-mode="true"' in client.get('/').text
 result=client.post('/api/debug/jump',json={'section':'identity_theft'}).json()
 for value in ['continue','no','no']:
  result=client.post('/api/advance',json={**{k:result[k] for k in ['history','revision','debug_section']},'value':value}).json()
 assert result['page']['node_id']=='identity_recognized_choice'
 assert result['page']['title']=='Do you want to raise an Identity Theft defense?'
 assert app.state.collection is None and not directory.exists()


def test_other_nineteen_defenses_keep_their_existing_nodes_and_routes():
 nodes=[n.model_dump() for n in TREE.nodes if n.discussion_topic not in {'Identity Theft','Wrong Party'}]
 digest=hashlib.sha256(json.dumps(nodes,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 assert digest=='1bf90b16ca7ab0f1a5586595e11c277899a9e9f02d56a0faa9f6c4513f56381b'


def test_collection_records_recognized_choice_and_recalculates_after_an_edit(tmp_path):
 from test_research_collection import context,rows
 from test_guided_november_scripts import reach as normal_reach
 module=runpy.run_path(str(ROOT/'scripts/run_clickthrough.py'))
 client=TestClient(module['create_app'](collection_dir=tmp_path))
 current=normal_reach('identity_theft',recognize='yes')
 current=step(step(current,'no'),'no')
 assert current.current=='identity_recognized_choice'
 history=[a.model_dump(mode='json') for a in current.history]
 sid=str(uuid4())
 assert client.post('/api/state',json={'session_id':sid,'history':history}).status_code==200
 response=client.post('/api/advance',json={'history':history,'value':'yes','collection':context(sid)})
 assert response.status_code==200,response.text
 result=response.json()
 assert result['page']['node_id']=='identity_recognized_notice'
 assert rows(tmp_path,'defenses.csv')[0]['DEFENSE.identity_theft.CHECKED']=='Yes'
 index=next(i for i,a in enumerate(result['history']) if a['node_id']=='identity_recognized_choice')
 response=client.post('/api/edit',json={'history':result['history'],'revision':result['revision'],
     'edit_index':index,'value':'no','collection':context(sid)})
 assert response.status_code==200,response.text
 assert response.json()['page']['input_type']=='summary'
 events=rows(tmp_path,'responses.csv')
 choices=[r for r in events if r['RESPONSE.ITEM.ID']=='identity_recognized_choice']
 assert [r['RESPONSE.ITEM.VALUE'] for r in choices]==['yes','no']
 assert [r['RESPONSE.EVENT.TYPE'] for r in choices]==['First submission','User change']
 combined=[r for r in events if r['RESPONSE.ITEM.ID']=='CHECKBOX.identity_theft.main']
 assert [r['RESPONSE.ITEM.VALUE'] for r in combined]==['include','exclude']
 assert all(r['RESPONSE.EVENT.TYPE']=='Program calculation' for r in combined)
 assert rows(tmp_path,'defenses.csv')[0]['DEFENSE.identity_theft.CHECKED']=='No'
