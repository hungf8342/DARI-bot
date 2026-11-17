#!/usr/bin/env python3
"""Extract paragraph/list structure from the approved Word source without flattening it."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/source-material/2026-11.14/2026.11.14 Affirmative-Defense-Scripts.docx'
SOL_SOURCE = ROOT / 'docs/source-material/2026-11-15/2026.11.15 Affirmative-Defense-Scripts-v3.docx'
SHARED_SOURCE = ROOT / 'docs/source-material/2026-11-15/2026.11.15 Affirmative-Defense-Scripts-v4.docx'
OUTPUT = ROOT / 'src/advocate_bot_qualtrics/practice_areas/consumer_debt/script_formatting.yaml'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{'+NS['w']+'}'


def accepted_xml(data: bytes) -> ET.Element:
    """Read Word's accepted revision view without modifying the source document.

    Insertions and moved-to text remain; deleted/moved-from text and historical
    formatting properties must not leak into text, lists, or screen references.
    """
    root = ET.fromstring(data)
    removed = {W + name for name in ('del', 'moveFrom', 'rPrChange', 'pPrChange')}
    for parent in root.iter():
        for child in list(parent):
            if child.tag in removed:
                parent.remove(child)
    return root


def extract_formatting(source: Path) -> dict:
    with ZipFile(source) as document:
        root = accepted_xml(document.read('word/document.xml'))
        numbering = ET.fromstring(document.read('word/numbering.xml'))
        footnotes = accepted_xml(document.read('word/footnotes.xml'))
    headers = {}
    for note in footnotes:
        text = ''.join(node.text or '' for node in note.findall('.//w:t', NS)).strip()
        if text.startswith('NEW SCREEN:'):
            headers[note.get(W+'id')] = text.removeprefix('NEW SCREEN:').strip()
    abstract = {node.get(W+'abstractNumId'): {
        level.get(W+'ilvl'):level.find('w:numFmt',NS).get(W+'val')
        for level in node.findall('w:lvl',NS)} for node in numbering.findall('w:abstractNum',NS)}
    numbers = {node.get(W+'numId'):node.find('w:abstractNumId',NS).get(W+'val')
               for node in numbering.findall('w:num',NS)}
    paragraphs = []
    quoted = False
    for index, paragraph in enumerate(root.findall('.//w:p',NS)):
        text = ''.join(node.text or '' if node.tag==W+'t' else '\n' if node.tag==W+'br' else '\t'
                       for node in paragraph.iter() if node.tag in {W+'t',W+'br',W+'tab'})
        style = paragraph.find('w:pPr/w:pStyle',NS)
        runs = [run for run in paragraph.findall('.//w:r',NS) if ''.join(run.itertext()).strip()]
        bold = bool(runs) and all(run.find('w:rPr/w:b',NS) is not None and
                run.find('w:rPr/w:b',NS).get(W+'val') not in {'0','false'} for run in runs)
        if bold or (style is not None and style.get(W+'val','').startswith('Heading')):
            quoted = False
        # Repair a missing space in the November 10 source's SOL introduction.
        text = text.strip().replace('variesdepending', 'varies depending')
        # A reviewer-outline bullet can contain the beginning of a reply that
        # continues in the next paragraph. It is not a user-facing list item.
        quote_container = text.startswith('“')
        if text.startswith('“'):
            quoted = True
            text = text[1:]
        if quoted and text.endswith('”'):
            text = text[:-1]
            quoted = False
        if not text.strip():
            continue
        entry = {'text':text.strip(), 'source_index':index}
        references = [node.get(W+'id') for node in paragraph.findall('.//w:footnoteReference', NS)]
        if references:
            entry['screen_footnotes'] = references
        num = paragraph.find('w:pPr/w:numPr',NS)
        if num is not None:
            level = num.find('w:ilvl',NS).get(W+'val','0')
            number = num.find('w:numId',NS).get(W+'val')
            entry.update(list_level=int(level), list_format=abstract[numbers[number]][level])
            if quote_container:
                entry['quote_container'] = True
        paragraphs.append(entry)
    return {'source':str(source.relative_to(ROOT)), 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'paragraphs':paragraphs, 'screen_headers':headers}


def serialize(data):
    return '# Generated from Nov 14 later defenses, Nov 15 v3 defenses 1–5, and v4 shared/identity/wrong-party content.\n'+yaml.safe_dump(data,sort_keys=False,allow_unicode=True,width=100)


def extract_prototype_formatting():
    """Combine approved v4 shared/identity content, v3 defenses 1–5, and Nov 14 later defenses."""
    data = extract_formatting(SOURCE)
    earlier = extract_formatting(SOL_SOURCE)
    latest = extract_formatting(SHARED_SOURCE)

    def at(document, heading):
        return max(i for i, item in enumerate(document['paragraphs']) if item['text'] == heading)

    sections = [
        (latest, latest['paragraphs'][:at(latest, '1 Statute of Limitations')], 'v4:'),
        (earlier, earlier['paragraphs'][at(earlier, '1 Statute of Limitations'):at(earlier, '6 Identity Theft')], 'v3:'),
        (latest, latest['paragraphs'][at(latest, '6 Identity Theft'):at(latest, '8 Laches')], 'v4:'),
    ]
    old_end = at(data, '8 Laches')
    obsolete = {key for item in data['paragraphs'][:old_end] for key in item.get('screen_footnotes', [])}
    for key in obsolete:
        data['screen_headers'].pop(key, None)
    paragraphs = []
    for document, items, prefix in sections:
        for original in items:
            item = {**original, 'source': document['source']}
            if document is earlier and (78 <= item['source_index'] <= 93 or 249 <= item['source_index'] <= 262):
                item['internal'] = True
            if 'screen_footnotes' in item:
                for reference in item['screen_footnotes']:
                    data['screen_headers'][prefix + reference] = document['screen_headers'][reference]
                item['screen_footnotes'] = [prefix + key for key in item['screen_footnotes']]
            paragraphs.append(item)
    data['paragraphs'][:old_end] = paragraphs
    for key, document in [('sol_source', earlier), ('revision_source', earlier),
                          ('shared_source', latest), ('identity_source', latest), ('wrong_party_source', latest)]:
        data[key] = document['source']
        data[key + '_sha256'] = document['source_sha256']
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    content=serialize(extract_prototype_formatting())
    if args.check:
        if OUTPUT.read_text(encoding='utf-8') != content:
            raise SystemExit('Formatting differs from the approved Nov 14, Nov 15 v3, and v4 source sections. Regenerate it.')
    else:
        OUTPUT.write_text(content,encoding='utf-8')


if __name__=='__main__':
    main()
