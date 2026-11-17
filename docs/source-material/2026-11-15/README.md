# November 15 affirmative-defense scripts

All four Word documents were copied unchanged from Windows Downloads. Their
original tracked changes and comments are preserved. SHA-256 fingerprints:

| Document | SHA-256 |
| --- | --- |
| `2026.11.15 Affirmative-Defense-Scripts.docx` | `0f76875c465ff4de28571eb7cceee40753ecfd12cdfd9b2487bc1c4361fa605f` |
| `2026.11.15 Affirmative-Defense-Scripts-v2.docx` | `721ccb3dbd8e06934d610a554a9081fc7c7ac1a03ce844fd3c003ac2a94392f1` |
| `2026.11.15 Affirmative-Defense-Scripts-v3.docx` | `885412a6ca9fb67cd55541a190e002d54bf12412094488ef6b713c57fce337d3` |
| `2026.11.15 Affirmative-Defense-Scripts-v4.docx` | `efb4a8ec395449f61d46feb92a96ded3406432c5df9c5bd503aa70bd1be59f1a` |

## Current source boundaries

- Shared steps, Identity Theft, and Wrong Party: accepted v4 revisions.
- SOL, Ambiguity, Standing/Privity, Failure to State a Cause of Action, Mistake:
  accepted v3 revisions, preserving the work requested in the previous update.
- Defenses 8–21: November 14 wording and routes, with current shared review rules.
- Preliminary intake: October 30. Structure/field tables are author-facing and
  do not become litigant questions.

The extractor records each revised paragraph's source path and original index.
V3 footnotes use `v3:` keys and v4 footnotes use `v4:` keys; later November 14
footnote IDs are retained. Each source's SHA-256 is recorded in formatting
metadata. Renumbered v4 footnotes for later defenses do not replace those defenses.

## Shared selections and confirmation

An explicit child selection selects every ancestor in `checkbox_parents`, never
siblings. Derived parents are recalculated after answers and edits. Removing the
last selected child removes an automatic parent; an independent parent Yes stays.
The former shared main-checkbox instruction is integrated into Confirm selections.

Selected reviews show numbered nested options and a reminder naming the main
checkbox after the visual. Empty reviews have no reminder. `confirmation_reminders`
allows a complete replacement sentence per defense; `[DEFENSE NAME]` is replaced
with its main checkbox name. Clarification remains non-advancing and records no
answer until an explicit form submission.

## Identity Theft — v4

Everyone first answers the stolen-card question. Yes and No each lead to their
approved guidance and a separate explicit Identity Theft choice. Not sure opens
clarification and returns to the question. The approved clinic notice has its own
screen when selected.

Then reuse verified account recognition. Both recognized and unrecognized
accounts receive another explicit Identity Theft choice, with their respective
guidance. V4 replaces the former recognized-account finish with this choice and
a conditional clinic notice. Missing/uncertain recognition returns to intake.

As confirmed by the user, these reasons are independent: either Yes keeps the
physical Identity Theft box selected. A later No does not erase another reason's
Yes. Each reason has its own Change control. Clinic checkpoints inspect the
combined selection; they do not change the user's choices.

## Wrong Party — v4

If Identity Theft was selected, first show its Wrong Party guidance and explicit
choice. V4 says **Yes finishes Wrong Party immediately**: preserve the selected
box and show its review, without asking the recognition branch. This supersedes
the earlier v3 instruction to ask both grounds after Yes.

No continues to verified recognition. If Identity Theft was not selected, go
directly to recognition. Both recognized and unrecognized accounts receive an
explicit Wrong Party choice, followed by the approved clinic notice when selected.
Unknown recognition returns to intake; uncertain choices require clarification.
Separate choices remain recorded and editable, and any Yes selects their shared
physical box. Edits remove choices that no longer belong on the revised path.

## Retained earlier revisions

SOL keeps the calendar-year cutoff and explicit main choice for every resolved
timing outcome, including recent payments. Recent timing suggests skipping;
older/uncertain timing suggests raising. Unknown timing is never restated as a
confirmed date. Only main Yes opens the grouped California/Delaware choices and
then the oral-contract choice, which appears on oral and written paths. The
unchanged dependency table does not override the revised body instructions.

Standing/Privity debt buyers receive separate ownership-claim and ownership-proof
choices. Original-creditor cases first choose the main defense, then its two
arguments independently if selected. Main No skips them.

Cause of Action uses substantive argument questions and the v3 wording. Its
separate Breach/Common Counts parent-instruction screens are folded into shared
confirmation. Known negative guidance still offers choices where the script says
to record them. The two Common Counts write-in reasons share the third physical
checkbox and remain independently editable. Complaint dates are restated in the
source order; the July 1, 2024 condition remains strictly after that date.

## Research records and browser versions

Normal collection keeps individual answers, calculated `CHECKBOX.<defense>.<box>`
values, and aggregate defense outcomes. Calculated selections are program events,
not fabricated user answers. SQLite remains authoritative. Source fingerprints,
old sessions, and historical response events are preserved; old versions are not
rewritten. V4 uses a fresh browser storage key to prevent obsolete routes from
bypassing new questions. Debug mode disables collection.

```bash
.venv/bin/python scripts/extract_script_formatting.py
.venv/bin/python scripts/extract_script_formatting.py --check
```
