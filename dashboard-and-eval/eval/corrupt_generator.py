"""
Corruption Generator for Evaluation — Person C

Generates synthetic hallucinated claims by applying three families of transformations
to correct legal claims:

  1. corrupt_fact(claim, field)      — swap a numeric/temporal value
  2. corrupt_entity(claim, entity_type) — swap a named legal entity
  3. negate_claim(claim)             — logical negation of the claim

Used by:
  - eval/gold_set generation (offline, build-time)
  - run_eval.py to expand the gold set with known negatives

Returns:
  str — the corrupted claim text
  The original claim is never modified.
"""

import random
import re


# ── Fact Corruption ────────────────────────────────────────────────────────────

# Pools of plausible but wrong values for each field type
_SECTION_NUMBERS = [
    "43", "43A", "43B", "66", "66A", "66B", "66C", "66D", "66E", "66F",
    "67", "67A", "67B", "69", "69A", "69B", "70", "72", "72A", "79",
    "1983", "1985", "1986", "12", "14", "21",
]
_YEARS = [
    "1966", "1967", "1973", "1984", "1986", "1988", "1990", "1995",
    "2000", "2002", "2005", "2008", "2011", "2013", "2016", "2019", "2021", "2023",
]
_PENALTIES = [
    "₹25,000", "₹50,000", "₹1 lakh", "₹2 lakh", "₹5 lakh", "₹10 lakh",
    "$5,000", "$10,000", "$50,000", "$100,000",
    "3 years imprisonment", "5 years imprisonment", "7 years imprisonment",
    "life imprisonment",
]
_DURATIONS = ["30 days", "60 days", "90 days", "6 months", "1 year", "2 years", "3 years"]

_FACT_POOLS: dict[str, list[str]] = {
    "section": _SECTION_NUMBERS,
    "year": _YEARS,
    "penalty": _PENALTIES,
    "duration": _DURATIONS,
}


def corrupt_fact(claim: str, field: str = "auto") -> str:
    """
    Swap a numeric or temporal value in the claim with a plausible but wrong one.

    Args:
        claim: The original legal claim text.
        field: One of 'section', 'year', 'penalty', 'duration', or 'auto'
               (auto-detects based on claim content).

    Returns:
        Corrupted claim string, or original claim if no match found.

    Examples:
        >>> corrupt_fact("Section 43A of the IT Act...", "section")
        "Section 66C of the IT Act..."
        >>> corrupt_fact("Miranda v. Arizona (1966)", "year")
        "Miranda v. Arizona (1984)"
    """
    if field == "auto":
        field = _auto_detect_field(claim)
        if field is None:
            return claim  # nothing to corrupt

    pool = _FACT_POOLS.get(field, [])
    if not pool:
        return claim

    if field == "section":
        # Replace section numbers like "43A", "Section 43A", "§ 43A"
        match = re.search(r"(?:Section\s+|§\s*)?(\d+[A-Za-z]*)", claim, re.IGNORECASE)
        if match:
            original = match.group(1)
            replacement = _pick_different(pool, original)
            return claim.replace(original, replacement, 1)

    elif field == "year":
        match = re.search(r"\b(1[89]\d{2}|20[012]\d)\b", claim)
        if match:
            original = match.group(1)
            replacement = _pick_different(pool, original)
            return claim.replace(original, replacement, 1)

    elif field in ("penalty", "duration"):
        # Try to replace any existing penalty/duration token, else append
        for token in pool:
            if token in claim:
                replacement = _pick_different(pool, token)
                return claim.replace(token, replacement, 1)
        # No existing token — append a wrong value as a suffix corruption
        wrong = random.choice(pool)
        return f"{claim.rstrip('.')} (incorrect penalty: {wrong})."

    return claim


def _auto_detect_field(claim: str) -> str | None:
    """Guess which field is most corruption-worthy in this claim."""
    if re.search(r"(?:Section|§)\s*\d+", claim, re.IGNORECASE):
        return "section"
    if re.search(r"\b(1[89]\d{2}|20[012]\d)\b", claim):
        return "year"
    if any(t in claim for t in ["₹", "$", "imprisonment", "penalty", "fine"]):
        return "penalty"
    if re.search(r"\b\d+\s+(days|months|years)\b", claim, re.IGNORECASE):
        return "duration"
    return None


def _pick_different(pool: list[str], exclude: str) -> str:
    """Pick a random value from pool that is different from exclude."""
    candidates = [v for v in pool if v != exclude]
    return random.choice(candidates) if candidates else random.choice(pool)


# ── Entity Corruption ─────────────────────────────────────────────────────────

_COURTS = [
    "Supreme Court", "High Court", "District Court", "Sessions Court",
    "National Consumer Disputes Redressal Commission", "Cyber Appellate Tribunal",
    "Circuit Court of Appeals", "Court of Appeals", "Federal District Court",
]
_JUDGES = [
    "Justice Chandrachud", "Justice Khanna", "Justice Kaul",
    "Chief Justice Sanjiv Khanna", "Justice B.R. Gavai",
    "Chief Justice Warren", "Justice Brennan", "Justice Marshall",
    "Justice Blackmun", "Justice O'Connor",
]
_PARTIES = [
    "State of Maharashtra", "Union of India", "State of Gujarat",
    "Shreya Singhal", "Anuradha Bhasin", "Puttaswamy",
    "Miranda", "Gideon", "Mapp", "Terry", "Escobedo",
]
_ACTS = [
    "IT Act 2000", "IT Amendment Act 2008", "IPC", "CrPC", "Evidence Act",
    "Data Protection Act", "GDPR", "CCPA", "HIPAA",
    "Fourth Amendment", "Fifth Amendment", "Sixth Amendment", "Fourteenth Amendment",
]

_ENTITY_POOLS: dict[str, list[str]] = {
    "court": _COURTS,
    "judge": _JUDGES,
    "party": _PARTIES,
    "act": _ACTS,
}


def corrupt_entity(claim: str, entity_type: str = "auto") -> str:
    """
    Swap a named legal entity (court, judge, party, act) with a plausible wrong one.

    Args:
        claim:       The original legal claim text.
        entity_type: One of 'court', 'judge', 'party', 'act', or 'auto'.

    Returns:
        Corrupted claim string, or original if no entity matched.

    Examples:
        >>> corrupt_entity("The Supreme Court held that...", "court")
        "The High Court held that..."
    """
    if entity_type == "auto":
        entity_type = _auto_detect_entity(claim)
        if entity_type is None:
            return claim

    pool = _ENTITY_POOLS.get(entity_type, [])
    if not pool:
        return claim

    # Try to find and replace the first occurrence of any pool member
    for entity in pool:
        if entity.lower() in claim.lower():
            idx = claim.lower().find(entity.lower())
            replacement = _pick_different(pool, entity)
            return claim[:idx] + replacement + claim[idx + len(entity):]

    # No pool member found — inject one
    replacement = random.choice(pool)
    return f"{claim.rstrip('.')} [entity corrupted: {replacement}]."


def _auto_detect_entity(claim: str) -> str | None:
    """Guess which entity type is most prominent in this claim."""
    claim_lower = claim.lower()
    if any(c.lower() in claim_lower for c in _COURTS):
        return "court"
    if any(j.lower() in claim_lower for j in _JUDGES):
        return "judge"
    if any(a.lower() in claim_lower for a in _ACTS):
        return "act"
    if any(p.lower() in claim_lower for p in _PARTIES):
        return "party"
    return None


# ── Negation Corruption ───────────────────────────────────────────────────────

# Pairs: (pattern, replacement) — tries each in order, uses first match
_NEGATION_RULES: list[tuple[str, str]] = [
    (r"\bdoes not require\b", "requires"),
    (r"\brequires\b", "does not require"),
    (r"\bshall not\b", "shall"),
    (r"\bshall\b", "shall not"),
    (r"\bmust not\b", "must"),
    (r"\bmust\b", "must not"),
    (r"\bis prohibited\b", "is permitted"),
    (r"\bis permitted\b", "is prohibited"),
    (r"\bis not\b", "is"),
    (r"\bis\b", "is not"),
    (r"\bdoes not\b", "does"),
    (r"\bdoes\b", "does not"),
    (r"\bcannot\b", "can"),
    (r"\bcan\b", "cannot"),
    (r"\billegal\b", "legal"),
    (r"\blegal\b", "illegal"),
    (r"\bvalid\b", "invalid"),
    (r"\binvalid\b", "valid"),
    (r"\bguarantees\b", "does not guarantee"),
    (r"\bprotects\b", "does not protect"),
    (r"\bprohibits\b", "permits"),
    (r"\bpermits\b", "prohibits"),
]


def negate_claim(claim: str) -> str:
    """
    Logically negate a legal claim by applying the first matching negation rule.

    If no pattern matches, prepends "It is incorrect that " to the claim.

    Args:
        claim: The original legal claim text.

    Returns:
        Negated claim string.

    Examples:
        >>> negate_claim("Section 43A requires data controllers to compensate victims.")
        "Section 43A does not require data controllers to compensate victims."
        >>> negate_claim("The right to privacy is a fundamental right.")
        "The right to privacy is not a fundamental right."
    """
    for pattern, replacement in _NEGATION_RULES:
        if re.search(pattern, claim, re.IGNORECASE):
            match = re.search(pattern, claim, re.IGNORECASE)
            return claim[: match.start()] + replacement + claim[match.end():]

    # Fallback: wrap the whole claim
    return f"It is incorrect that {claim[0].lower()}{claim[1:]}"


# ── Convenience: apply all three ──────────────────────────────────────────────

def corrupt_all(claim: str) -> list[dict]:
    """
    Apply all three corruption strategies and return a list of corrupted variants.

    Returns:
        List of dicts: [{"strategy": str, "corrupted_claim": str}, ...]
    """
    return [
        {"strategy": "corrupt_fact", "corrupted_claim": corrupt_fact(claim)},
        {"strategy": "corrupt_entity", "corrupted_claim": corrupt_entity(claim)},
        {"strategy": "negate_claim", "corrupted_claim": negate_claim(claim)},
    ]
