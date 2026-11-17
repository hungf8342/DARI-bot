"""Accepted Word revisions, all 21 defenses, and the November 14 routing decisions."""
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import runpy
from uuid import uuid4
from zipfile import ZipFile

import pytest

from advocate_bot_qualtrics.practice_areas.consumer_debt.debug_navigation import jump_to_section
from advocate_bot_qualtrics.practice_areas.consumer_debt.workflow import (
    CONTENT, CONTINUE_PAGES, DEFENSES, TREE, ClickthroughReview, GuidedAdvanceRequest,
    GuidedEditRequest, advance_review, edit_review,
)
from advocate_bot_qualtrics.practice_areas.consumer_debt.script_formatting import SOURCE_FORMATTING
from advocate_bot_qualtrics.practice_areas.consumer_debt.research_collection import ResearchCollection
from test_clickthrough_workflow import intake

ROOT = Path(__file__).resolve().parents[1]


def start(defense, **changes):
    creditor = changes.pop('guided_creditor_type', 'buyer')
    history = intake(creditor)[:-2]
    history = [answer.model_copy(update={'value': changes.get(answer.node_id, answer.value)}) for answer in history]
    return jump_to_section(ClickthroughReview().replay(history), defense)


def step(current, value='continue'):
    return advance_review(current.defaults, GuidedAdvanceRequest(
        history=current.history, revision=current.revision, debug_section=current.debug_section, value=value))


def reach(current, node, choices=None):
    choices = choices or {}
    for _ in range(120):
        if current.current == node:
            return current
        value = choices.get(current.current, 'continue' if current.current in CONTINUE_PAGES else 'no')
        current = step(current, value)
    pytest.fail(f'Failed to reach {node}, stopped at {current.current}')


def test_word_revision_view_omits_deletions_moves_and_historical_formatting(tmp_path):
    module = runpy.run_path(str(ROOT / 'scripts/extract_script_formatting.py'))
    source = tmp_path / 'tracked.docx'
    w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    with ZipFile(source, 'w') as document:
        document.writestr('word/document.xml', f'''<w:document xmlns:w="{w}"><w:body><w:p>
          <w:r><w:t>Current </w:t></w:r>
          <w:del><w:r><w:t>deleted text </w:t><w:footnoteReference w:id="2"/></w:r></w:del>
          <w:moveFrom><w:r><w:t>old location </w:t></w:r></w:moveFrom>
          <w:ins><w:r><w:t>inserted </w:t></w:r></w:ins>
          <w:moveTo><w:r><w:t>moved</w:t><w:footnoteReference w:id="1"/></w:r></w:moveTo>
          <w:pPr><w:pPrChange><w:pPr><w:numPr><w:numId w:val="99"/></w:numPr></w:pPr></w:pPrChange></w:pPr>
          </w:p></w:body></w:document>''')
        document.writestr('word/numbering.xml', f'<w:numbering xmlns:w="{w}"/>')
        document.writestr('word/footnotes.xml', f'''<w:footnotes xmlns:w="{w}"><w:footnote w:id="1"><w:p>
          <w:r><w:t>NEW SCREEN: Current heading</w:t></w:r><w:del><w:r><w:t>deleted heading</w:t></w:r></w:del>
          </w:p></w:footnote></w:footnotes>''')
    module['extract_formatting'].__globals__['ROOT'] = tmp_path
    result = module['extract_formatting'](source)
    assert result['paragraphs'] == [{'text': 'Current inserted moved', 'source_index': 0, 'screen_footnotes': ['1']}]
    assert result['screen_headers'] == {'1': 'Current heading'}


def test_current_document_keeps_tracked_changes_and_metadata_uses_accepted_text():
    source = ROOT / CONTENT['source']
    assert source.name == '2026.11.14 Affirmative-Defense-Scripts.docx'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_FORMATTING['source_sha256']
    with ZipFile(source) as document:
        xml = document.read('word/document.xml')
    assert b'<w:ins ' in xml and b'<w:del ' in xml
    sol = CONTENT['nodes']['statute_of_limitations_intro']['explanation']
    assert 'Even if [PLAINTIFF] sued within the time limit' not in sol
    assert 'Consider raising this defense' in sol
    assert 'seek more information' in CONTENT['nodes']['sol_buyer']['question']
    assert len(DEFENSES) == 21
    assert [value['number'] for value in DEFENSES.values()] == list(range(1, 22))


@pytest.mark.parametrize('ownership', ['yes', 'no'])
@pytest.mark.parametrize('proof', ['yes', 'no'])
def test_standing_buyer_can_choose_both_nested_boxes_regardless_of_attachments(ownership, proof):
    current = start('standing_privity', guided_ownership_claim=ownership, guided_ownership_proof=proof)
    current = reach(current, 'standing_first')
    assert ('This argument will not work if' in ' '.join(current.page()['body'])) == (ownership == 'yes')
    assert not current.session.checkbox_selections
    current = step(current, 'yes')
    assert current.current == 'standing_second_buyer'
    current = step(current, 'no')
    assert current.current == DEFENSES['standing_privity']['summary']
    assert current.session.checkbox_selections['standing_privity'] == {'first':'include','second':'exclude','main':'include'}


def test_standing_original_creditor_has_explicit_main_choice_with_skip_guidance():
    current = reach(start('standing_privity', guided_creditor_type='original'), 'standing_original_choice')
    assert 'may not apply' in ' '.join(current.page()['body'])
    assert len(TREE.node(current.current).selection_checkboxes) == 1
    current = step(current, 'no')
    assert current.session.checkbox_selections['standing_privity'] == {'main':'exclude'}


@pytest.mark.parametrize('recognized', ['yes', 'no'])
def test_identity_no_stolen_card_offers_an_explicit_choice_before_recognition(recognized):
    current=reach(start('identity_theft',guided_recognize=recognized),'identity_stolen_card')
    current=step(current,'no')
    assert current.current=='identity_negative_choice'
    assert not current.session.checkbox_selections
    assert 'nobody stole your card' in ' '.join(current.page()['body'])
    current=step(current,'no')
    assert current.current==('identity_recognized_choice' if recognized=='yes' else 'identity_account_choice')


def test_identity_uncertainty_is_not_no_and_returns_to_the_stolen_card_question():
    current = reach(start('identity_theft'), 'identity_stolen_card')
    current = step(current, 'unknown')
    assert current.page()['title'] == 'Ready to return to the pending question?'
    assert current.session.defense_open_questions
    assert not current.session.checkbox_selections
    assert step(current).current == 'identity_stolen_card'


@pytest.mark.parametrize('choice', ['yes','no'])
def test_identity_choice_is_explicit_and_clinic_notice_is_a_separate_screen(choice):
    current=reach(start('identity_theft',guided_recognize='yes'),'identity_stolen_card')
    current=step(current,'yes')
    assert current.current=='identity_theft_decision' and not current.session.checkbox_selections
    current=step(current,choice)
    if choice=='yes':
        assert current.current=='identity_clinic_notice'
        assert 'ask clinic staff' in ' '.join(current.page()['body'])
        current=step(current)
    assert current.current=='identity_recognized_choice'
    assert current.session.checkbox_selections['identity_theft']['main']==('include' if choice=='yes' else 'exclude')
    current=step(current,'no')
    if choice=='yes':
        assert current.current=='identity_recognized_notice'
        current=step(current)
    assert current.current==DEFENSES['identity_theft']['summary']
    current=step(step(current))
    assert current.current==('wrong_party_identity_choice' if choice=='yes' else 'wrong_party_recognized_choice')


def test_wrong_party_unrecognized_account_can_select_then_gets_clinic_guidance():
    current = reach(start('wrong_party', guided_recognize='no'), 'wrong_party_account_choice')
    assert 'similar name' in ' '.join(current.page()['body'])
    current = step(current, 'yes')
    assert current.current == 'wrong_party_clinic_notice'
    assert current.session.checkbox_selections['wrong_party']['main'] == 'include'


@pytest.mark.parametrize('creditor', ['original','buyer'])
def test_cause_ownership_choices_apply_to_debt_buyers_only(creditor):
    current = start('failure_to_state_cause', guided_creditor_type=creditor)
    nodes=[]
    for _ in range(80):
        nodes.append(current.current)
        if current.current == DEFENSES['failure_to_state_cause']['summary']:
            break
        current=step(current, 'continue' if current.current in CONTINUE_PAGES else 'no')
    else:pytest.fail('Cause section did not complete')
    assert ('cause_breach_second_buyer' in nodes) == (creditor=='buyer')
    assert 'cause_breach_second_original' not in nodes
    assert 'cause_common_second_original' not in nodes


def test_common_counts_third_checkbox_combines_two_independent_write_in_reasons():
    current=start('failure_to_state_cause', guided_suit_type='common', guided_statement='no',
                  guided_ownership_proof='no', guided_payment_date='2024-07-02')
    current=reach(current,'cause_common_attachment_checkbox')
    current=step(current,'yes')
    assert current.current=='cause_recent_debt_choice'
    assert 'notify clinic staff' in ' '.join(current.page()['body'])
    current=step(current,'yes')
    assert current.current==DEFENSES['failure_to_state_cause']['summary']
    choices=current.session.checkbox_selections['failure_to_state_cause']
    assert choices['common_third_ownership']==choices['common_third_recent_debt']==choices['common_third']=='include'
    rows=current.page()['rows']
    assert len([r for r in rows if r['id']=='common_third'])==1
    row=next(r for r in rows if r['id']=='common_third')
    assert 'no proof of plaintiff ownership' in row['label']
    assert 'debt incurred after July 1, 2024' in row['label']
    assert len(row['write_in_reasons'])==2
    assert len({reason['edit_index'] for reason in row['write_in_reasons']})==2
    assert not any(r['id'] in {'common_third_ownership','common_third_recent_debt'} for r in rows)
    assert len([r for r in current.review_answers('failure_to_state_cause') if r['node_id'] in {'cause_common_attachment_checkbox','cause_recent_debt_choice'}])==2


@pytest.mark.parametrize('payment,breach,offered', [('2024-07-01','missing',False),('2024-07-02','missing',True),('missing','2024-07-02',True)])
def test_common_counts_date_check_uses_either_complaint_date_and_strict_source_cutoff(payment,breach,offered):
    current=start('failure_to_state_cause', guided_creditor_type='original', guided_suit_type='common',
                  guided_payment_date=payment,guided_breach_date=breach)
    current=step(step(current))
    assert (current.current=='cause_recent_debt_choice')==offered
    if offered:
        assert '[BREACH.DATE]' not in ' '.join(current.page()['body'])
        assert '2024-07-02' in ' '.join(current.page()['body'])


def test_unknown_complaint_fact_returns_to_intake_without_becoming_a_negative():
    current=start('failure_to_state_cause',guided_ownership_claim='unknown')
    current=reach(current,'guided_ownership_claim')
    assert current.pending_preliminary_route=='cause_breach_owner_gate'
    current=step(current,'unknown')
    assert current.current=='guided_ownership_claim'
    current=step(current,'yes')
    assert current.current=='cause_breach_second_buyer'


def test_common_counts_only_identity_option_depends_on_selection_not_suspicion():
    for selected in ['yes','no']:
        current=start('identity_theft',guided_suit_type='both')
        current=reach(current,'identity_theft_decision',{'identity_stolen_card':'yes'})
        current=step(current,selected)
        visited=[]
        for _ in range(160):
            visited.append(current.current)
            if current.current==DEFENSES['common_counts']['summary']:break
            current=step(current,'continue' if current.current in CONTINUE_PAGES else 'no')
        else:pytest.fail('Did not reach Common Counts review')
        assert ('common_counts_fourth_checkbox' in visited)==(selected=='yes')


def test_old_collection_rows_survive_adding_four_defenses(tmp_path):
    collector=ResearchCollection(tmp_path)
    sid=uuid4();collector.start(sid)
    with collector.connect() as db:
        data=json.loads(db.execute('SELECT data FROM sessions WHERE id=?',(str(sid),)).fetchone()[0])
        for name in ('standing_privity','failure_to_state_cause','identity_theft','wrong_party'):
            data['defenses'].pop(name)
        data['session']['SESSION.TREE.VERSION']='historical-17-defense-version'
        data['values']['legacy-answer']='yes'
        collector.save(db,sid,data)
    collector.start(sid)
    with collector.connect() as db:
        restored=json.loads(db.execute('SELECT data FROM sessions WHERE id=?',(str(sid),)).fetchone()[0])
    assert restored['values']['legacy-answer']=='yes'
    assert restored['session']['SESSION.TREE.VERSION']=='historical-17-defense-version'
    assert all(restored['defenses'][name]['CHECKED']=='' for name in ('standing_privity','failure_to_state_cause','identity_theft','wrong_party'))


def test_original_creditor_missing_and_unknown_are_distinct_in_the_new_checks():
    current=start('failure_to_state_cause',guided_original_creditor='unknown')
    current=reach(current,'guided_original_creditor')
    page=current.page()
    assert page['allow_unknown'] and page['allow_text_missing']
    assert step(current,'unknown').current=='guided_original_creditor'
    current=step(current,'missing')
    assert current.current=='cause_breach_first'
    entry=current.session.preliminary_fields['ORIGINAL.CREDITOR']
    assert entry.complaint_status=='missing' and entry.complaint_value is None
    assert 'did not identify' in ' '.join(current.page()['body'])


def test_identity_selection_edit_invalidates_wrong_party_and_common_counts_only_options():
    current=reach(start('identity_theft',guided_suit_type='both'),'identity_theft_decision',{'identity_stolen_card':'yes'})
    current=step(current,'yes')
    current=reach(current,'common_counts_fourth_checkbox',{'wrong_party_identity_choice':'yes'})
    current=step(current,'yes')
    current=reach(current,DEFENSES['common_counts']['summary'])
    index=next(i for i,a in enumerate(current.history) if a.node_id=='identity_theft_decision')
    current=edit_review({},GuidedEditRequest(history=current.history,edit_index=index,value='no',debug_section='identity_theft'))
    current=reach(current,DEFENSES['common_counts']['summary'])
    assert current.session.checkbox_selections.get('wrong_party',{}).get('main')!='include'
    assert current.session.checkbox_selections['common_counts'].get('fourth')!='include'
    assert not any(a.node_id=='common_counts_fourth_checkbox' for a in current.history)


def test_date_edit_removes_one_write_in_reason_but_keeps_the_shared_box_selected():
    current=start('failure_to_state_cause',guided_suit_type='common',guided_statement='no',guided_ownership_proof='no',guided_payment_date='2024-07-02')
    current=reach(current,'cause_common_attachment_checkbox')
    current=step(current,'yes');current=step(current,'yes');current=step(current)
    index=next(i for i,a in enumerate(current.history) if a.node_id=='guided_payment_date')
    current=edit_review({},GuidedEditRequest(history=current.history,edit_index=index,value='2024-07-01',debug_section='failure_to_state_cause'))
    current=reach(current,DEFENSES['failure_to_state_cause']['summary'])
    choices=current.session.checkbox_selections['failure_to_state_cause']
    assert choices['common_third']=='include'
    assert choices['common_third_ownership']=='include'
    assert 'common_third_recent_debt' not in choices
    row=next(row for row in current.page()['rows'] if row['id']=='common_third')
    assert row['checked'] and 'no proof of plaintiff ownership' in row['label']
    assert 'debt incurred after July 1, 2024' not in row['label']
    assert any(change['label']=='Debt incurred after July 1, 2024' and change['after']=='Not offered on this path'
               for change in current.page()['changes'])


@pytest.mark.parametrize('defense',['standing_privity','failure_to_state_cause','identity_theft','wrong_party'])
def test_new_section_clarification_cannot_record_choices_or_advance(defense,tmp_path):
    from fastapi.testclient import TestClient
    from advocate_bot_qualtrics.core.schemas import ChatTurnResponse
    module=runpy.run_path(str(ROOT/'scripts/run_clickthrough.py'))
    module['create_app'].__globals__['submit_chat_turn']=lambda **kwargs:ChatTurnResponse(
        user_intent='answer_node',assistant_reply='Select it.',next_node_id='yes')
    client=TestClient(module['create_app'](debug=True,collection_dir=tmp_path/'research'))
    current=start(defense)
    payload={'history':[a.model_dump(mode='json') for a in current.history],'debug_section':defense}
    before=client.post('/api/state',json=payload).json()
    reply=client.post('/api/help',json={**payload,'question':'Explain this defense'})
    assert reply.status_code==200 and reply.json()['next_node_id'] is None
    assert reply.json()['user_intent']!='answer_node'
    assert client.post('/api/state',json=payload).json()==before
    assert not (tmp_path/'research').exists()


def test_browser_missing_original_creditor_and_shared_write_in_edit_controls():
    import shutil
    import subprocess
    if shutil.which('node') is None:
        pytest.skip('Node is needed for the browser harness')
    script=r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const nodes=new Map();
function make(){const n={children:[],listeners:{},validity:{valid:true},append(...c){this.children.push(...c)},replaceChildren(...c){this.children=c},addEventListener(k,f){this.listeners[k]=f},setAttribute(){},focus(){},close(){}};
Object.defineProperty(n,'id',{set(id){this._id=id;nodes.set(id,this)},get(){return this._id}});return n}
function node(id){if(!nodes.has(id))nodes.set(id,make());return nodes.get(id)}
const context=vm.createContext({
 document:{getElementById(id){return id.startsWith('text-')?nodes.get(id)||null:node(id)},createElement(){return make()},querySelector(){return null},querySelectorAll(){return []},addEventListener(){}},
 window:{addEventListener(){},scrollTo(){}},sessionStorage:{getItem(){return null},setItem(){}},
 crypto:{randomUUID(){return 'id'}},fetch(){return new Promise(()=>{})},setTimeout(){return 1},clearTimeout(){},AbortController,
});
vm.runInContext(fs.readFileSync('scripts/assets/clickthrough/app.js','utf8'),context);
vm.runInContext("page={node_id:'guided_original_creditor',input_type:'text',field_label:'Original creditor',allow_unknown:true,allow_text_missing:true,default_value:'missing'};history=[];cursor=0;updateAnswerResponse=()=>{};inputControls()",context);
assert.equal(nodes.get('text-missing').checked,true);assert.equal(nodes.get('text-answer').disabled,true);
assert.equal(vm.runInContext('selectedValue()',context),'missing');
nodes.get('text-unknown').checked=true;nodes.get('text-unknown').listeners.change();
assert.equal(nodes.get('text-missing').checked,false);assert.equal(vm.runInContext('selectedValue()',context),'unknown');
nodes.get('text-missing').checked=true;nodes.get('text-missing').listeners.change();
assert.equal(nodes.get('text-unknown').checked,false);assert.equal(vm.runInContext('selectedValue()',context),'missing');
nodes.get('text-missing').checked=false;nodes.get('text-missing').listeners.change();nodes.get('text-answer').value='Example Bank';
assert.equal(nodes.get('text-answer').disabled,false);assert.equal(vm.runInContext('selectedValue()',context),'Example Bank');
const table=vm.runInContext(`summaryTable({section:'Failure to State a Cause of Action',rows:[{
 label:'Common Counts third checkbox',detail:'Nested checkbox',checked:true,status:'Selected',edit_index:3,
 write_in_reasons:[{label:'No proof of plaintiff ownership',value:'Include this reason',edit_index:3},{label:'Debt incurred after July 1, 2024',value:'Include this reason',edit_index:8}]
}]})`,context);
function all(n){return [n,...n.children.flatMap(all)]}
const marks=all(table).filter(n=>(n.className||'').startsWith('selection-mark'));
const buttons=all(table).filter(n=>n.textContent==='Change');
assert.equal(marks.length,1);assert.equal(buttons.length,2);
vm.runInContext('goto=(index)=>{globalThis.changedIndex=index}',context);
buttons[0].onclick();assert.equal(context.changedIndex,3);buttons[1].onclick();assert.equal(context.changedIndex,8);
'''
    result=subprocess.run(['node','-e',script],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
