# Guided affirmative-defense prototype

Run with the development/demo environment:

```bash
.venv/bin/python scripts/run_clickthrough.py
```

Open <http://localhost:7861/>. The server binds to localhost and defaults to the
imaginary original-creditor complaint. Use `--complaint-fields PATH` for another
fact-only example or `--blank` to start without prefilled examples.

## Source and scope

The current governing source is [the November 14 script](source-material/2026-11.14/2026.11.14%20Affirmative-Defense-Scripts.docx).
Defenses 1–5 use [November 15 v3](source-material/2026-11-15/2026.11.15%20Affirmative-Defense-Scripts-v3.docx).
Shared steps, Identity Theft, and Wrong Party use [November 15 v4](source-material/2026-11-15/2026.11.15%20Affirmative-Defense-Scripts-v4.docx).
Defenses 8–21 retain November 14 wording and routing.
The prototype includes all 21 defenses in Attachment 4 order. Preliminary intake retains its 18 October 30 fields and separate
review.

The November 14 `NEW SCREEN:` footnotes determine headers and screen boundaries,
with defenses 1–5 from v3 and shared steps/Identity Theft/Wrong Party from v4.
Revised references use `v3:` and `v4:` keys to preserve later source IDs.
`screen_layout.yaml` maps their IDs to the prototype's nodes and conditional
variants; `script_formatting.yaml` extracts the actual headers, source
paragraph indices, paragraph/list structure, and document fingerprint. All 145 source header references are accounted for, including retained metadata
for parent screens now merged into confirmation. The Common Counts Only fourth nested checkbox is offered when the user selected
Identity Theft. Reported suspicion alone does not select or offer that checkbox. Mistake has no new
footnote and retains its combined explanation/checkbox screen under its name.

A new screen's explanation stays with that screen and does not appear as feedback
on the question leading to it. When the source supplies a response without a new
screen (such as the SOL payment acknowledgments), it remains inline after answer
selection. Draft previews never record facts, choices, or research events.
Changing a selection replaces its preview. Next records the answer and advances.
Paragraphs, lists, indentation, and full-month date formatting are preserved.

Introductions remain separate where screening follows. Ambiguity, Mistake, and
Unconscionable Contract keep their explanation and checkbox question together.
No-offer results with their own footnotes are informational screens with Next,
followed by review. Failure to Mitigate, Common Counts, and Excuse derive their main checkboxes
from explicit nested choices. Their shared main-checkbox reminder now appears
on Confirm selections, with no extra main-checkbox instruction screen.

Summary checklists use ordinal numbers and the source’s descriptive nested-option labels in each
defense and the final review. Failure to Mitigate asks about the declined settlement
offer first, shows its checkbox guidance or inapplicability result, then asks about
contact and shows the second checkbox’s result. This order applies with and without
a debt consolidation company.

Capacity has an Account opening date screen between its introduction and age
question. Oral Modification has a Contract Change screen only when the user
previously reported an agreed change that was not honored. Conditional creditor,
consolidation, and language text uses confirmed session facts. Unknowns remain
separate from No. Shared clarification uses its source header and Next returns to
the pending question. Staff referrals still require explicit resolution.

Common Counts' first nested checkbox and Excuse's second and fifth are offered
without additional screening, as directed by the script. Common Counts' fifth
nested checkbox depends on the user's explicit Fraud selection. Its fourth nested
checkbox is not offered. The language section asks whether the creditor gave the
translated agreement; No can lead to an offer, while Yes finishes without one.
Missing language is collected before language-specific questions.

Each section ends in its own summary or no-offer result page. The final review
shows all 21 defenses, nested options, selections, and unresolved questions. Case
details remain accessible throughout. Short answers and date/amount formats follow
the preliminary script. Browser progress is tab-local; the v4 update uses
a new storage key to start a fresh review instead of importing an obsolete path.

## Current shared steps and Standing/Privity

The shared parent-selection step records all ancestors of an explicitly selected
reason without selecting siblings. Derived parents are recalculated after answers
and edits. A parent selected independently remains selected when its last child
is removed. Declining a directly offered parent skips its children.

Confirm selections contains the checkbox visual and a named main-checkbox reminder
only when something is selected. Nested rows show `(1)`, `(2)`, etc. alongside
their descriptions. A defense may supply its own complete reminder sentence in
`confirmation_reminders`; otherwise the shared default names its main checkbox.
The former shared parent-instruction screen is folded into this review.
Identity Theft and Wrong Party show separately editable reasons for their shared
physical checkbox. Any Yes selects it; uncertainty remains separately recorded.

Standing/Privity original-creditor cases now ask about the main defense, then two
separate arguments if selected. Both arguments show the revised original-creditor
skip guidance. Debt-buyer cases keep separate claim/proof choices with the new
wording. Every uncertain choice requires clarification. The current source and
binding details are in [the November 15 source notes](source-material/2026-11-15/README.md).

## November 14 routing decisions retained for other defenses

All tracked insertions/deletions are read in Word's accepted revision view. The
source `.docx` retains its tracked changes and comments. Reviewer comments are
context; unresolved legal questions in comments do not become new screening rules.

Standing/Privity asks about the first nested box for debt buyers whether the
ownership allegation is present or missing, with the corresponding guidance. The
second nested box is offered for every debt buyer regardless of attachments.
Original-creditor Standing/Privity routing uses the retained main
choice and separate argument choices described above.

Failure to State a Cause of Action now follows the revised Breach of Contract
and Common Counts groups. Buyer-only ownership checks stay buyer-only; known
negative screening guidance still leaves checkbox choices to the user. Unknown
complaint contents return to intake. Either a complaint payment date or breach
date strictly after July 1, 2024 offers the new Common Counts write-in reason and
clinic guidance. As confirmed by the user, it shares the physical third checkbox
with “no proof of plaintiff ownership”; the two reasons are recorded independently
and either included reason checks that single box. Parent and main boxes derive
from explicit nested choices.

Identity Theft v4 offers explicit choices after either stolen-card answer and
for both recognized and unrecognized accounts. Either Yes keeps its shared box
selected, with each reason separately editable. Wrong Party v4 finishes immediately
after Yes on its Identity Theft path; No proceeds to an explicit recognition-based
choice. Recognized accounts are offered that choice too. Clinic notices follow
the selected-box checkpoints. See [current routing notes](source-material/2026-11-15/README.md).

A new browser storage key starts a fresh review for this source version. Existing
SQLite/CSV records and original tree-version values are preserved. The guide has
no supported cross-version resume from an old 17-defense browser path.

## Script wording and formatting

The approved Word documents govern wording and user-facing paragraph/list structure. The formatting extractor reads paragraphs, lists, and screen footnotes from November 14, combines v3 defenses 1–5 with v4 shared steps, Identity Theft, and Wrong Party, and records all three source fingerprints. Each revised paragraph carries its own source path and original paragraph index. `script_formatting.yaml` records source paragraphs, Word list
levels, and the source document's SHA-256 fingerprint. Regenerate and verify it with:

```bash
.venv/bin/python scripts/extract_script_formatting.py
.venv/bin/python scripts/extract_script_formatting.py --check
```

The renderer uses structured paragraphs and semantic HTML lists for explanations,
checkbox guidance, inline responses, and approved clarification text. Source
paragraph breaks receive visible paragraph spacing; lists remain lists. Source
paragraph boundaries are also restored where an earlier copy folded them together.
Reviewer-outline bullets around an entire quoted reply are not presented as
user-facing list items. The source's actual lists inside quoted explanations are
preserved, including their separate groups. Text is inserted safely as text.

The formatting layer preserves paragraphs and lists; the SOL adapter implements the November 15 screen boundaries and routing. Tests compare the generated metadata against this mixed source and verify that all 14 later defenses retain their nodes and routes.

## SOL screen placement

November 15 SOL footnotes define these screens and their headers. Bold directions remain internal;
paragraphs, lists, and indentation preserve source structure within each screen.

| Screen | Content and behavior |
| --- | --- |
| Statute of Limitations | General explanation; when the original-creditor complaint omits payment date, its missing-date guidance stays here. |
| Do you agree that your last payment date was [LAST.PAYMENT.DATE]? | Complaint date and months before filing; agreement or uncertainty acknowledgment appears inline. |
| Was your last payment after [filing date minus one calendar year]? | Yes means recent payment. No means payment on/before the cutoff. All three answers lead to an explicit main choice; Not sure remains recorded uncertainty. The matching acknowledgment appears inline. |
| Do you want to check off the Statute of Limitations checkbox? | Debt-buyer guidance with the explicit main-box choice; this source header is unchanged. |
| Do you want to raise a Statute of Limitations defense? | Original-creditor guidance: recent payments suggest skipping, qualifying/uncertain timing suggests raising. Yes opens nested choices; No opens confirmation. |
| Do you want to raise a Statute of Limitations defense for California and Delaware written contracts? | Combined checkbox guidance and choice. Continue to the matching oral/written second-checkbox screen. |
| Do you want to raise a Statute of Limitations defense for oral contracts? | Oral-contract guidance and explicit second-box choice. |
| Statute of Limitations defense for oral contracts | Written-contract inapplicability guidance followed by the same explicit oral-defense choice. Both Yes and No are recorded; uncertainty requires clarification. |
| Confirm selections | Separate review with the approved selected/empty wording, checkbox visual, evidence, and Change controls; also used when no boxes were offered. |
| Ready to return to the pending question? | Shared clarification wording, Ask a Question, and Next returning to the pending choice or unresolved preliminary field. No extra Yes/No response is required. |

The payment cutoff uses calendar years, including February 28 for a leap-day
anniversary. Editing the filing date invalidates a retained personal timing answer;
timing guidance uses the revised after-cutoff meaning. Recent timing still permits an explicit choice; an edit cannot automatically select or decline a box.
After Back/Change revisits payment timing, the main SOL checkbox screen appears
again before nested choices. A prior main-box choice is prefilled for review;
submitting it retains applicable nested choices. Back also visits every required screen still on the revised path. Retained answers prefill those screens; the browser waits for Next at each screen instead of jumping over reused answers. This applies across all defenses, including explanations and reviews.
Disagreeing with the complaint payment date, or answering Not sure, always shows
the personal cutoff-date question again. A saved personal timing answer may prefill
that screen only if the filing date is unchanged; it cannot bypass the question.
Displayed dates use full month names (for example, “September 20, 2025”), including headers, guidance, timelines, and case details. Date input controls and research values retain ISO formats.
The main SOL box is offered as an explicit choice; selecting a nested option also
selects its ancestors under the shared rule. Only Yes offers the nested SOL
choices; No removes dependent choices and goes directly to confirmation. The
first and third remain grouped, and the second is explicitly offered on either
oral or written paths. Changing between oral and written agreements requires
a new second-box answer because the guidance changes.
Unresolved creditor type, oral agreement, or missing filing date must be clarified
before the dependent questions proceed. Browser storage has a new v4 key so
saved paths cannot bypass the revised choices. Historical research records
remain preserved under their original tree versions.

## Ambiguity screen placement

The current Ambiguity section keeps the explanation with **Ask about this checkbox**,
then explicitly directs **Continue to “Confirm selections.”** Preserve these as
separate steps:

| Screen | Content | After answering |
| --- | --- | --- |
| Ambiguity checkbox | Full approved explanation and “Do you want to check off Ambiguity?” | Yes/No records the choice and advances; selection confirmation is not inline |
| Confirm selections | Selected/empty confirmation wording and Ambiguity checklist with Change | Continue to the next defense |

An undecided answer remains unresolved. Returning from clarification restores the
full explanation with the same checkbox question. Previews do not record a choice.

## Initial defense screens

Every defense starts with its source heading; the Fraud heading includes the November 14 punctuation. For defenses without
screening branches (Ambiguity, Mistake, and Unconscionable Contract), the full
November 14 explanation and checkbox question appear in the body on that screen.
Word bullet lists and paragraph spacing are preserved.

Laches has a separate general-explanation screen, headed “Laches,” followed by
its screening questions. The explanation is not repeated on the checkbox screen.
Its selection confirmation remains on the following review.

Saved introduction records for combined screens remain replayable and are skipped
by Back. Saved Laches paths from the briefly combined layout also remain usable.

The shared script note applies only to defenses without screening branches:
**Show the general explanation and checkbox question together on one screen,
with the defense name as the heading.** Defenses with screening branches retain
their separate explanation screens before the follow-up questions.

## Editing and clarification

Summary comparisons use earlier recorded choices or completed defense reviews.
Defenses reached for the first time after an edit do not show “Previously” labels
or an unchanged-selections notice.

Back preserves answers. Change replays the updated path, retaining applicable
facts and explicit choices. Newly relevant questions require an answer. A removed
checkbox choice is discarded when its section reaches review and is not restored
if another edit later makes that checkbox available. Changing an earlier defense
also reconciles dependent offers in later defenses. Finishing after an edit requires
a fresh summary confirmation.

SOL retains its dependency planner, conditional timing evidence, and grouped first
and third choice. Names are used for personalization. Qualifying timing comparisons
can be reused without inventing agreement with an edited exact date. Irrelevant
unknown Laches facts do not block an offer supported by another Yes.

“Ask a question” uses the current approved page context and confirmed facts. Its
response always has `next_node_id: null`; chat does not answer form questions or
advance the guide. Approved explanations stay available if the model is unavailable.

## Implementation

`defense_content.yaml` contains November 14 copy and route overrides, with
defenses 1–5 from v3 and shared steps/Identity Theft/Wrong Party from v4.
`screen_layout.yaml` maps the source footnotes to headers and informational screens.
`workflow.py` validates those overrides into a prototype-specific tree, renders
pages and clarification context from that tree, and replays validated histories.
`base_tree.yaml` remains the shared base tree for these overlays and
session bindings. Its historical node IDs are retained for validated replay.
`intake_fields.yaml` retains the October 30 intake. SOL's dependency
map remains in `sol_checkbox_dependencies.yaml` and `sol_dependency_map.py`.

`scripts/run_clickthrough.py` serves the form and clarification endpoints;
`scripts/assets/clickthrough/` contains the buildless browser assets. The progress
bar includes all sections and scrolls horizontally. The history limit accommodates
all 21 sections and clarification returns. `research_collection.py` collects the
research datasets below. `rendering.py` provides shared fact substitution. Tests cover source wording, allowed branches, full
traversal, no-offer outcomes, uncertainty, nested selections, editing, final review,
CSV collection, and non-advancing clarification.

The prototype performs no filing, document generation, Excel export, or account
storage. The deterministic form works without model calls; clarification chat uses
Z.ai through the OpenAI-compatible client. Research records persist locally on the server.

## Debug section navigation

```bash
.venv/bin/python scripts/run_clickthrough.py --debug
```

Debug mode displays a banner and makes the scrollable section header clickable,
including Preliminary fields and all 21 defenses. Both the numbered circle and
section name activate the link; controls briefly disable while a page loads.
Versioned asset URLs ensure a refresh loads updated navigation code. A header jump fills unanswered
intake fields and starts that section directly, without answering or completing
skipped defenses. Click Preliminary fields to inspect or change the case details.
An already visited section in the current path can be revisited with its answers;
a new jump starts the selected section fresh using the current confirmed intake.

On the first debug visit, confirmed intake from the normal tab progress is copied
into separate debug storage. Existing answers and a valid current intake draft
are preserved. Missing values use the loaded example complaint where available;
remaining fallbacks are in `debug_navigation.py`: an original creditor, both claim
types, $4,250, payment on March 15, 2021, filing on September 30, 2026, a recognized
account, a written agreement, and no debt-consolidation company. Both claim types
are used only when that field has not already been answered.

Advance, Back, Change, clarification, and reload work from the selected section.
The debug anchor is validated on every request. Header progress does not mark
skipped sections complete. Normal mode rejects debug jump requests and anchors.

Research collection is completely disabled in debug mode, including session start,
answer events, edits, and exit beacons. The debug server does not open or create
the research database or CSVs, even if a request includes collection metadata.
Normal browser progress and research files remain separate. Restart without
`--debug` to return to normal intake and collection.

## Research CSVs

Running the prototype without `--debug` automatically writes three UTF-8 CSVs to
`output/clickthrough/`. Use `--collection-dir PATH` to choose another directory.
All three use the requested variable names and share a random UUID `SESSION.ID`.
The defense names in column headers match the 21 IDs in `workflow.DEFENSES`.
All 21 defenses have columns in new datasets; newly added defense columns remain
blank for historical sessions that never reviewed them. When an existing collection
directory contains records from an older prototype, exports preserve its historical
defense columns and rows alongside the new columns.

- `sessions.csv`: one row per session, including sessions abandoned in intake.
  Start time is the first successful page request. Completion becomes Yes only
  after Finish review reaches the final page; editing an answer requires fresh
  completion. Merely navigating Back does not undo completion. The tree version
  contains the source date and a content fingerprint of the scripts and rules.
- `defenses.csv`: one row per session, with three columns per defense. CHECKED is
  Yes if any box for that defense is selected. TREE.PROJECTION is Yes if at least
  one checkbox is offered on the current reconciled path, regardless of the user's
  choice. Both stay blank while unresolved. Projection becomes Yes when the tree
  reaches an offered checkbox, or No when the defense finishes without an offer.
  CHECKED becomes Yes on any explicit inclusion; it becomes No after all offered
  choices are explicitly declined, or the defense finishes without an offer.
  CHANGED is 1
  once a User change event edits a field belonging to that defense.
  Shared preliminary edits count for the defenses that use those fields: creditor
  type for SOL, Fraud, and Waiver; claim type for Common Counts and Excuse;
  consolidation for Mitigation, Rescission, and Accord; recognition for Lack of
  Consideration; and opening date for Capacity. Independent preliminary fields and
  personalization-only names do not set a defense's CHANGED flag.
- `responses.csv`: an append-only event dataset. Preliminary item IDs use the
  field identifiers from `intake_fields.yaml`, such as `CASE.NUMBER`,
  `PLAINTIFF`, and `COMPLAINT.DATE` (the filing date). Defense questions and deterministic conditions
  use their tree node IDs. Derived original-creditor values and calculated
  `DEFENSE.<name>.CHECKED` / `TREE.PROJECTION` values are also recorded.
  Derived parents are recorded as program calculations with IDs
  `CHECKBOX.<defense>.<box>` and values `include` or `exclude`. Answers
  use their stored values (for example `yes`, `no`, `unknown`, or an ISO date).
  Each calculated field first appears only when its own result is determined.
  TREE.PROJECTION is recorded when the tree reaches a checkbox offer or completes
  a no-offer path. CHECKED is recorded after an explicit inclusion, after all
  offered choices are declined, or on completion of a no-offer path. No on the main SOL choice skips all nested choices and records
  CHECKED as No immediately. Recent-payment SOL paths still have a choice, so
  their TREE.PROJECTION is Yes even though the guidance suggests skipping. Starting a defense, incomplete screening, and uncertain
  checkbox answers do not create negative results. The defense CSV retains its
  one-row-per-session shape, with blank unresolved values.

The response columns, in order, are `SESSION.ID`, `RESPONSE.ITEM.ID`,
`RESPONSE.ITEM.VALUE`, `RESPONSE.EVENT.TYPE`, `RESPONSE.REVISION.NUMBER`,
`RESPONSE.START.TIME`, `RESPONSE.CHECK.TIME`, and `RESPONSE.END.TIME`.
The four event types are First submission, User change, Program calculation,
and Program invalidation. `RESPONSE.CALC.OR.INPUT` is no longer exported;
the event type identifies who produced the value.

Each item's first recorded value has revision 0; every subsequent change or
invalidation increments that item's revision independently. A Program invalidation
has an empty value. A new explicit answer after invalidation is a User change
event. Valid retained answers do not
produce duplicate submissions. Pending replay of a later defense is not treated
as invalidation. Back, opening Change, submitting an unchanged answer, navigation
screens, and clarification-chat messages do not create answer events.
If an edit makes a previously known defense result unresolved, the response log
records a Program invalidation and the defense CSV clears that field until a
new result is determined. Previously collected rows retain their original
values and timestamps; the new collection version starts a fresh browser review.

User response start time comes from when the browser renders that question.
Check time is the most recent answer selection or valid text/date/amount entry
on that page; end time comes from the click submitting it. Check time is NA if
the user accepts a prefilled value without interacting with the answer control.
These timestamps use the browser clock, normalized to UTC. Check time, when
present, must fall between start and end. Program calculations and invalidations
use the server clock and equal start/end times because they have no user display
interval; their check time is always NA. Session timestamps also use the server
clock. Unsubmitted drafts are not collected.

Start over ends the current session and creates a new UUID without deleting its
records. Closing or leaving the page sends a browser `pagehide` beacon to record
the end time. Reloading/restoring that tab keeps its UUID and clears the end time
while the session is active again. Browser shutdown, crashes, or a disconnected
server can prevent the exit beacon arriving; in that case SESSION.END.TIME stays
empty. Completion remains independently recorded even if exit reporting fails.

`collection.sqlite3` in the same directory is the authoritative local store.
Each accepted operation commits there before atomically replacing each CSV;
server startup rebuilds the CSVs from the database. Repeated delivery of the
same collection event ID is ignored. Use one prototype server per collection
directory. The `output/` directory is gitignored; Start over clears browser
progress but does not erase the collected CSVs or database.
