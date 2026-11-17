# November 10 affirmative-defense scripts

`2026.11.10 Affirmative-Defense-Scripts.docx` was the November 10 source for the guided
prototype's wording, paragraph/list formatting, screen footnotes, and nested
checkbox summary descriptors. The document is unchanged from Windows Downloads.

That revision retained defenses 1, 2, 5, 8, and 9–21. Defenses 3, 4, 6, and 7 remain
excluded, including the dependent Common Counts fourth checkbox.

Failure to Mitigate now completes the settlement-offer question and first-checkbox
result before the contact question and second-checkbox result, for both debt
consolidation paths. Summaries and final review use descriptive nested-option
labels. The wording changes include SOL, Ambiguity, Mistake, Laches, Fraud,
Capacity, Waiver, and the shared clarification instruction.

`screen_layout.yaml` maps the document's screen footnotes. The extractor
repairs the missing space in “variesdepending” in the SOL introduction; the Word
file itself is preserved.

Regenerate and check formatting metadata with:

```bash
.venv/bin/python scripts/extract_script_formatting.py
.venv/bin/python scripts/extract_script_formatting.py --check
```

The current application uses the [accepted November 14 revisions](../2026-11.14/README.md)
and includes all 21 defenses.

The shared base tree and October 30 preliminary-intake source remain separate
from the current guided defense overlays.
