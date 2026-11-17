"""Deterministic conditions and explicit choices for the October 25 clinic scripts.

The YAML owns approved wording and routing. These functions read confirmed facts
and record progress; only a user's answer to a checkbox node selects a box.
"""
from __future__ import annotations

from datetime import date
from advocate_bot_qualtrics.practice_areas.consumer_debt.session import InteractiveSessionState


DEFENSE_LABELS = {
    "statute_of_limitations": "Statute of limitations",
    "ambiguity": "Ambiguity",
    "standing_privity": "Standing/privity",
    "failure_to_state_cause": "Failure to State a Cause of Action",
    "mistake": "Mistake",
    "identity_theft": "Identity Theft",
    "wrong_party": "Wrong Party",
    "laches": "Laches",
    "fraud": "Fraud, Misrepresentation, Concealment",
    "failure_to_mitigate": "Failure to Mitigate",
    "common_counts": "Common Counts Only",
    "unconscionable_contract": "Unconscionable Contract",
    "rescission": "Rescission",
    "lack_of_consideration": "Lack of Consideration",
    "accord_satisfaction": "Accord and Satisfaction",
    "excuse_breach": "Excuse/Breach of Contract",
    "capacity": "Capacity",
    "waiver": "Waiver",
    "oral_modification": "Oral Modification",
    "tender_payment": "Tender of Payment",
    "language_1632": "Violation of Civil Code Section 1632 Regarding Language",
}

DOCUMENTED_DEFENSES = tuple(DEFENSE_LABELS)


def calendar_cutoff(filing: date, years: int) -> date:
    """Subtract calendar years, mapping a leap-day cutoff to February 28."""
    try:
        return filing.replace(year=filing.year - years)
    except ValueError:
        return filing.replace(year=filing.year - years, day=28)


def preliminary_value(session: InteractiveSessionState, tag: str) -> str | date | None:
    """Read only verified or manually supplied preliminary facts."""
    entry = session.preliminary_fields.get(tag)
    return entry.value if entry and entry.status == "known" else None


def complaint_payment(session: InteractiveSessionState) -> date | None:
    """The complaint's allegation is separate from the litigant's payment estimate."""
    entry = session.preliminary_fields.get("LAST-PAYMENT-DATE")
    if entry is None:
        return session.last_payment_complaint
    if entry.verification in {"pending", "unknown"}:
        return None
    value = entry.complaint_value
    return value if isinstance(value, date) and entry.complaint_status == "present" else None


def payment_comparison_branch(session: InteractiveSessionState) -> str:
    if complaint_payment(session) is not None and session.filing_date is not None:
        return "present"
    entry = session.preliminary_fields.get("LAST-PAYMENT-DATE")
    if entry and entry.complaint_status == "missing" and entry.verification not in {"pending", "unknown"}:
        return "missing"
    return "unknown"


def personalize(session: InteractiveSessionState, text: str) -> str:
    original_creditor = preliminary_value(session, "ORIGINAL.CREDITOR")
    if original_creditor is None and preliminary_value(session, "PLAINTIFF") == "original":
        original_creditor = preliminary_value(session, "PLAINTIFF-NAME")
    for token, tag, fallback in (
        ("[PLAINTIFF]", "PLAINTIFF-NAME", "the plaintiff"),
        ("[ORIGINAL.CREDITOR]", "ORIGINAL.CREDITOR", "the original creditor"),
    ):
        value = original_creditor if token == "[ORIGINAL.CREDITOR]" else preliminary_value(session, tag)
        text = text.replace(token, str(value or fallback))
    return text


def script_fact(session: InteractiveSessionState, key: str) -> str:
    """Read a confirmed fact for the October 25 scripts, preserving unknowns."""
    if key in session.script_facts:
        return session.script_facts[key]
    category, name = key.split(":", 1)
    if category == "answer":
        return session.defense_answers.get(name, "unknown")
    entry = session.preliminary_fields.get(name)
    if category == "field":
        return str(preliminary_value(session, name) or "unknown")
    if category != "complaint":
        raise ValueError(f"Unsupported script fact: {key}")
    if entry is None or entry.verification in {"pending", "unknown"}:
        return "unknown"
    if entry.complaint_status == "missing":
        return "no"
    if entry.complaint_status != "present":
        return "unknown"
    if name in {"OWNERSHIP", "OWNERSHIP.PROOF", "STATEMENT"}:
        return str(entry.complaint_value) if entry.complaint_value in {"yes", "no"} else "unknown"
    return "yes"


def script_condition(session: InteractiveSessionState, key: str) -> str:
    """Evaluate a declared script condition; YAML alone selects its next node."""
    if not key.startswith("rule:"):
        return script_fact(session, key)
    rule = key.removeprefix("rule:")
    if rule == "sol_timing_explicitly_uncertain":
        return "yes" if session.defense_answers.get("sol_payment_age") == "unknown" else "no"
    if rule == "payment_available":
        return payment_comparison_branch(session)
    if rule == "agreed_payment_age":
        payment, filing = complaint_payment(session), session.filing_date
        if payment is None or filing is None or payment > filing:
            return "unknown"
        return "yes" if payment <= calendar_cutoff(filing, 1) else "no"
    if rule == "language":
        language = session.primary_language
        return "english" if language and language.casefold() == "english" else "other" if language else "unknown"
    if rule == "standing_proof":
        return script_fact(session, "complaint:OWNERSHIP.PROOF") if script_fact(session, "field:PLAINTIFF") == "original" else "unknown"
    if rule in {"cause_both_dates_missing", "cause_attachments_missing"}:
        tags = ("LAST-PAYMENT-DATE", "BREACH-DATE") if rule == "cause_both_dates_missing" else ("STATEMENT", "OWNERSHIP.PROOF")
        values = [script_fact(session, "complaint:" + tag) for tag in tags]
        return "no" if "yes" in values else "yes" if values == ["no", "no"] else "unknown"
    if rule == "cause_recent_debt":
        tags = ("LAST-PAYMENT-DATE", "BREACH-DATE")
        for tag in tags:
            entry = session.preliminary_fields.get(tag)
            if (script_fact(session, "complaint:" + tag) == "yes" and entry
                    and isinstance(entry.complaint_value, date)
                    and entry.complaint_value > date(2024, 7, 1)):
                return "yes"
        return "unknown" if any(script_fact(session, "complaint:" + tag) == "unknown" for tag in tags) else "no"
    if rule in {"opening_date_known", "payment_date_known"}:
        tag = "OPEN-DATE" if rule == "opening_date_known" else "LAST-PAYMENT-DATE"
        entry = session.preliminary_fields.get(tag)
        return "yes" if (script_fact(session, "complaint:" + tag) == "yes"
                         and entry and isinstance(entry.complaint_value, date)) else "no"
    if rule == "identity":
        if "identity_stolen_card" in session.defense_answers:
            return session.defense_answers["identity_stolen_card"]
        suspicion = session.defense_answers.get("identity_suspected")
        if suspicion in {"yes", "no"}:
            return suspicion
        return "no" if script_fact(session, "field:RECOGNIZE") == "yes" else "unknown"
    if rule == "fraud":
        if script_condition(session, "rule:identity") == "yes":
            return "yes"
        return session.defense_answers.get("fraud_hidden_facts", "unknown")

    def any_yes(keys: list[str]) -> str:
        values = [script_condition(session, k) for k in keys]
        return "yes" if "yes" in values else "unknown" if "unknown" in values else "no"

    if rule == "laches":
        return any_yes(["answer:" + n for n in ("laches", "laches_statements", "laches_lost_info")])
    if rule == "mitigation":
        contact = script_fact(session, "answer:mitigation_contact")
        settlement = script_fact(session, "answer:mitigation_settlement")
        return "yes" if contact == "no" or settlement == "yes" else "no" if contact == "yes" and settlement == "no" else "unknown"
    if rule == "common_counts":
        return any_yes(["answer:" + n for n in ("common_counts_uncredited", "common_counts_renege", "common_counts_insurance")] + ["rule:identity", "rule:fraud"])
    if rule == "excuse":
        return any_yes(["answer:" + n for n in ("excuse_unconsented_change", "excuse_uncredited", "excuse_modified", "excuse_insurance", "excuse_unreasonable")])
    if rule in {"cause_breach_matches", "cause_common_matches"}:
        # Missing and uncertain complaint contents remain separate. A known
        # matching deficiency can offer a box, but uncertainty alone cannot.
        def absent(tag: str) -> bool | None:
            return {"yes": False, "no": True}.get(script_fact(session, "complaint:" + tag))

        def both_absent(first: str, second: str) -> bool | None:
            values = [absent(first), absent(second)]
            return False if False in values else None if None in values else True

        creditor = script_fact(session, "field:PLAINTIFF")
        if creditor not in {"original", "buyer"}:
            return "unknown"
        missing = [absent("OWNERSHIP")]
        if creditor == "buyer":
            missing.extend([absent("ORIGINAL.CREDITOR"), both_absent("STATEMENT", "OWNERSHIP.PROOF")])
        if rule == "cause_breach_matches":
            missing.extend([absent("OPEN-DATE"), both_absent("LAST-PAYMENT-DATE", "BREACH-DATE")])
        return "yes" if True in missing else "unknown" if None in missing else "no"
    raise ValueError(f"Unsupported script rule: {rule}")


def sync_combined_checkbox_choices(session: InteractiveSessionState, structures: dict) -> None:
    """Keep distinct explicit reasons; any Yes selects their shared physical box."""
    for defense, boxes in structures.items():
        for box, nodes in boxes.items():
            answers = [session.defense_answers[node] for node in nodes if node in session.defense_answers]
            if not answers:
                continue
            choices = session.checkbox_selections.setdefault(defense, {})
            if "yes" in answers:
                choices[box] = "include"
            elif "unknown" in answers:
                choices.pop(box, None)
            else:
                choices[box] = "exclude"
            if box == "main":
                if box in choices:
                    session.defense_selections[defense] = choices[box]
                else:
                    session.defense_selections.pop(defense, None)


def sync_checkbox_parents(session: InteractiveSessionState, structures: dict, *, tree, defense=None, final=False) -> None:
    """Derive ancestors from explicit choices without selecting sibling reasons.

    Rebuild derived values so removing a child cannot leave a stale parent. A
    parent's independent Yes survives removal of its last selected child.
    """
    nodes = tree.node_map
    for name, parents in structures.items():
        if defense is not None and name != defense:
            continue
        choices = session.checkbox_selections.get(name)
        if choices is None:
            if not final:
                continue
            choices = session.checkbox_selections.setdefault(name, {})
        explicit = {}
        for node_id, answer in session.defense_answers.items():
            node = nodes.get(node_id)
            if node and answer in {"yes", "no"}:
                for box in node.selection_checkboxes:
                    if box.defense_id == name:
                        explicit[box.checkbox_id] = "include" if answer == "yes" else "exclude"
        for parent in set(parents.values()):
            choices.pop(parent, None)
        choices.update(explicit)

        def resolve(box):
            children = [child for child, parent in parents.items() if parent == box]
            values = [resolve(child) for child in children]
            own = explicit.get(box) if children else choices.get(box)
            result = "include" if own == "include" or "include" in values else own
            if result is None and children and (all(v == "exclude" for v in values)
                    or (final and any(v is not None for v in values))):
                result = "exclude"
            if result is not None:
                choices[box] = result
            return result

        resolve("main")
        if final and "main" not in choices:
            choices["main"] = "exclude"
        if "main" in choices:
            session.defense_selections[name] = choices["main"]
        else:
            session.defense_selections.pop(name, None)


def run_script_action(session: InteractiveSessionState, action: str, *, tree=None) -> str:
    """Record workflow progress without turning screening facts into selections."""
    from advocate_bot_qualtrics.practice_areas.consumer_debt.base_tree import BASE_TREE_DEFINITION

    tree = tree or BASE_TREE_DEFINITION
    operation, defense, *parts = action.split(":")
    definition = next(node for node in tree.nodes if node.action == action)
    session.script_visited.append(definition.id)
    if operation == "script_finish":
        session.defense_results[defense] = {"status": "finished", "reason": definition.question}
    elif operation == "script_parent":
        group = "breach" if "breach" in definition.id else "common"
        choices = session.checkbox_selections.setdefault(defense, {})
        if group == "common":
            reasons = ("common_third_ownership", "common_third_recent_debt")
            if any(key in choices for key in reasons):
                choices["common_third"] = "include" if any(choices.get(key) == "include" for key in reasons) else "exclude"
        nested = [value for key, value in choices.items() if key.startswith(group + "_") and key != group + "_parent"]
        choices[group + "_parent"] = "include" if "include" in nested else "exclude"
        choices["main"] = "include" if any(value == "include" for key, value in choices.items() if key != "main") else "exclude"
        session.defense_selections[defense] = choices["main"]
    elif operation == "script_confirm":
        session.defense_results[defense] = {"status": "confirmed", "reason": "Choices confirmed by the user."}
    elif operation == "script_issue":
        key = parts[0]
        help_node = tree.node(definition.next)
        retry = next((b.target for b in help_node.branches if b.id == "retry"), "")
        session.defense_open_questions[key] = {"defense": defense, "reason": definition.question, "retry_node": retry}
        session.defense_results[defense] = {"status": "unresolved", "reason": definition.question}
    elif operation == "script_resolve":
        session.defense_open_questions.pop(parts[0], None)
        session.defense_results[defense] = {"status": "referred", "reason": "The user confirmed that clinic staff addressed this issue."}
    elif operation != "script_say":
        raise ValueError(f"Unsupported script action: {action}")
    return ""
