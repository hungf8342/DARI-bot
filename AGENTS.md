# Advocate Bot Qualtrics — Agent Guide

## Environment and common commands

Use Python 3.11 or newer and the gitignored `.venv/` interpreter explicitly;
agent command sessions may be fresh shells.

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev,demo]"
.venv/bin/python -m pytest
.venv/bin/python scripts/run_clickthrough.py
.venv/bin/python scripts/run_clickthrough.py --debug
.venv/bin/python scripts/extract_script_formatting.py --check
```

Activation is optional for interactive human terminals. On Windows, use
`.venv\Scripts\python.exe` in place of `.venv/bin/python`.

## Scope

- The clickthrough is the application to use and build on. Entry point:
  `scripts/run_clickthrough.py`; UI: `scripts/assets/clickthrough/`;
  workflow: `practice_areas/consumer_debt/workflow.py` under the package.
- The conversation engine, `process_chat`, bundle registry, Gradio interface,
  confidence scoring, and Excel export have been removed. Do not restore them
  as dependencies of the clickthrough. The pre-removal snapshot is `b7a72b0`.
- `base_tree.yaml` is still the shared base tree. Guided content/layout
  overlays, additional nodes, and answer bindings depend on its node IDs. Keep it and its source
  documents; do not prune nodes merely because the interface skips them.
- Current defense wording/formatting follows the accepted tracked changes in the
  November 14 source for defenses 8–21; defenses 1–5 follow November 15 v3;
  shared steps, Identity Theft, and Wrong Party follow November 15 v4.
  Preliminary fields follow October 30. Read
  `docs/source-material/2026-11.14/README.md` for retained routing choices and
  `docs/source-material/2026-11-15/README.md` for current source/routing details.
- Screening rules belong in `affirmative_defenses.py`; page traversal and edits
  belong in `workflow.py`; text substitution lives in `rendering.py`.
- Document extraction, autonomous traversal, account sign-in, and cross-device
  resume are not implemented.

## Data contract

- Facts come from submitted form answers. Requests replay validated history into
  a session. Example defaults are not effective facts until submitted.
- The clickthrough filing-date field is `COMPLAINT.DATE`, bound to the internal
  `FILING-DATE` field and `session.filing_date` for SOL screening.
- Unknown, missing, and No remain distinct. Explicit user choices select
  checkboxes and automatically select their ancestors in `checkbox_parents`. Never
  select sibling reasons automatically. Changes retain independent answers and
  invalidate affected results; independently selected parents survive removal of
  their last selected child.
- Separate Identity Theft and Wrong Party choices remain independent recorded
  answers; any Yes selects their shared physical checkbox. V4 Wrong Party ends
  immediately after Yes on the Identity Theft path; No proceeds to recognition.
- Normal mode collects through `research_collection.py`: SQLite is authoritative,
  with session, defense, and longitudinal response CSV exports. Use one server
  process per collection directory. Preserve historical research records.
- Debug mode disables collection and keeps separate browser progress.

## Clarification chat

- Keep structured responses with `user_intent`, `assistant_reply`, and
  `next_node_id`. Clarification must not record answers or advance the guide;
  `next_node_id` must be `null` in its API response.
- Use only the current approved page context and recorded facts. Keep approved
  explanations available when the provider is unavailable.
- The optional provider is Z.ai through the OpenAI-compatible client. Form
  traversal and research collection require no model calls.

## Repository safety

- Never commit `.env` or generated files in `output/`.
- Keep `.env.example` secret-free and do not change local credentials.
- Preserve approved Word source documents and formatting metadata.

## Testing

- Add or update tests whenever node schemas, routing validation, or prompts change.
- Keep shared rule/intake tests independent of a conversational engine.
- Cover valid branch constraints, terminal completion, summaries/open questions,
  edits/retained answers/invalidations, collection persistence, debug isolation,
  and non-advancing clarification.
- Collection fingerprints include source files; test version transitions while
  retaining historical records when changing those sources.
