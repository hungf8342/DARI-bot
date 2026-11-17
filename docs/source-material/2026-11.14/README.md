# November 14 affirmative-defense scripts

`2026.11.14 Affirmative-Defense-Scripts.docx` was copied unchanged from Windows
Downloads. It remains the source for the 14 later clickthrough defenses.
Shared steps and defenses 1–7 are superseded by the [November 15 update](../2026-11-15/README.md). Its original
tracked changes and comments are preserved; the source SHA-256 is
`3b303e4a96b345b8c20b51ccbfd425bd47a09104e0ad63e12f8de40c77126ddb`.

The formatting extractor reads the accepted revision view: insertions and moved-to
text are included, deletions, moved-from text, and historical formatting changes
are excluded. Source paragraphs, lists, footnotes, and the raw document fingerprint
are saved in `script_formatting.yaml`. Reviewer directions and comments are not
shown as user-facing text. A malformed `PLAINTIFF]` substitution token in the
Common Counts attachment paragraph is rendered as `[PLAINTIFF]` in the overlay.

Historical November 14 implementation decisions (Identity Theft routing is
superseded by the current v4 update linked above):

- Include all 21 defenses, including Failure to State a Cause of Action.
- Follow the literal Identity Theft sequence despite its contradictory later
  recognition clauses: ask about a stolen card first; No finishes, Yes offers an
  explicit choice and separate clinic notice before review. Unknown requires
  clarification. Do not bypass this sequence using account recognition.
- Treat the two Failure to State a Cause of Action/Common Counts third-checkbox
  write-ins as independent reasons under the same physical checkbox. Either
  included reason checks it; both reasons remain individually editable.

The source's July 1, 2024 date condition is implemented as **after** that date,
using either included complaint date. A reviewer comment says “on or after,” but
that unresolved difference does not override the body of the document.

The November 14 SOL version used independent main and nested choices; the
November 15 v3/v4 updates now requires main selection before nested choices. Its
calendar-year timing screen remains. Shared identity-dependent offers
use explicit selections where the revised script says “checked off,” including
Wrong Party and the fourth Common Counts Only checkbox.

Preliminary intake retains the October 30 script; the original-creditor text field
now distinguishes a name, “Not listed in the complaint,” and “I’m not sure” so
new complaint-presence checks can preserve the missing/unknown distinction.

Regenerate and check accepted formatting metadata with:

```bash
.venv/bin/python scripts/extract_script_formatting.py
.venv/bin/python scripts/extract_script_formatting.py --check
```
