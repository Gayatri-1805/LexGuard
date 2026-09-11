"""
Comprehensive Test Cases for Legal Hallucination Detection System
==================================================================

Test Coverage:
- Complete hallucinations (obvious false claims)
- Partial hallucinations (mix of accurate and false information)
- Accurate statements (fully correct legal information)
- Edge cases (ambiguous, complex, multi-section references)
- Negation tests (correctly stating what sections DON'T cover)
- Numerical accuracy (precise punishment details)
"""

COMPREHENSIVE_TEST_CASES = [
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 1: COMPLETE HALLUCINATIONS (Should be FLAGGED)
    # ═══════════════════════════════════════════════════════════════
    {
        "id": "hallucination_001",
        "category": "hallucinated",
        "expected_decision": "FLAGGED",
        "text": "Section 43 of the Information Technology Act, 2000 prescribes criminal prosecution with mandatory imprisonment for data breaches, with sentences ranging from 5 to 10 years.",
        "description": "Section 43 is civil liability only, not criminal - completely false imprisonment claims",
        "difficulty": "easy",
        "false_claims": ["criminal prosecution", "mandatory imprisonment", "5 to 10 years"],
        "truth": "Section 43 provides civil compensation only, no criminal penalties"
    },
    {
        "id": "hallucination_002",
        "category": "hallucinated",
        "expected_decision": "FLAGGED",
        "text": "Under Section 66 of the IT Act, cyber terrorism is punishable by life imprisonment and a fine of up to Rs. 10 crores.",
        "description": "Section 66 is about hacking, not cyber terrorism; wrong punishment details",
        "difficulty": "easy",
        "false_claims": ["cyber terrorism", "life imprisonment", "Rs. 10 crores"],
        "truth": "Section 66 covers computer-related offenses, max 3 years imprisonment and Rs. 5 lakh fine"
    },
    {
        "id": "hallucination_003",
        "category": "hallucinated",
        "expected_decision": "FLAGGED",
        "text": "Section 79 of the IT Act makes intermediaries criminally liable for all third-party content, requiring them to monitor and filter all user posts before publication.",
        "description": "Section 79 provides safe harbor, not criminal liability; no pre-monitoring requirement",
        "difficulty": "medium",
        "false_claims": ["criminally liable for all content", "pre-publication filtering"],
        "truth": "Section 79 provides safe harbor for intermediaries under specific conditions"
    },
    {
        "id": "hallucination_004",
        "category": "hallucinated",
        "expected_decision": "FLAGGED",
        "text": "The Information Technology Act, 2000 Section 85 allows government to shut down any website without judicial oversight for a period of up to 6 months.",
        "description": "No Section 85 with such powers exists",
        "difficulty": "hard",
        "false_claims": ["Section 85", "shutdown without oversight", "6 months"],
        "truth": "Blocking powers are under Section 69A with procedural safeguards"
    },
    {
        "id": "hallucination_005",
        "category": "hallucinated",
        "expected_decision": "FLAGGED",
        "text": "According to Section 43A, companies that suffer data breaches must pay a mandatory fine of Rs. 50 lakhs to the government within 30 days of discovery.",
        "description": "Section 43A provides for compensation to affected persons, not government fines",
        "difficulty": "medium",
        "false_claims": ["mandatory fine to government", "Rs. 50 lakhs", "30 days timeline"],
        "truth": "Section 43A mandates compensation to affected individuals, amount determined by adjudicator"
    },

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 2: PARTIAL HALLUCINATIONS (Should be ABSTAIN)
    # ═══════════════════════════════════════════════════════════════
    {
        "id": "partial_001",
        "category": "partially_hallucinated",
        "expected_decision": "ABSTAIN",
        "text": "Section 67 of the Information Technology Act, 2000 punishes the publishing or transmitting of obscene material in electronic form. On the first conviction, the punishment may extend to three years' imprisonment and a fine of up to ten lakh rupees.",
        "description": "Correct about obscene material provision, but fine amount is wrong (should be Rs. 5 lakh)",
        "difficulty": "medium",
        "accurate_parts": ["Section 67", "obscene material", "electronic form", "three years"],
        "false_parts": ["ten lakh rupees fine"]
    },
    {
        "id": "partial_002",
        "category": "partially_hallucinated",
        "expected_decision": "ABSTAIN",
        "text": "Section 67A deals with sexually explicit content involving children. The punishment includes imprisonment up to five years and fine up to one crore rupees on first conviction.",
        "description": "Correct subject matter but wrong punishment details (fine is Rs. 10 lakh, not 1 crore)",
        "difficulty": "medium",
        "accurate_parts": ["Section 67A", "sexually explicit content", "children", "five years"],
        "false_parts": ["one crore rupees"]
    },
    {
        "id": "partial_003",
        "category": "partially_hallucinated",
        "expected_decision": "ABSTAIN",
        "text": "Under Section 66B, whoever dishonestly receives stolen computer resources or communication devices is liable for imprisonment up to three years or fine up to one lakh rupees or both.",
        "description": "Correct section and subject, but fine amount is wrong (should be Rs. 1 lakh, imprisonment details may vary)",
        "difficulty": "hard",
        "accurate_parts": ["Section 66B", "stolen computer resources", "dishonestly receives"],
        "false_parts": ["specific fine amount may be inaccurate"]
    },
    {
        "id": "partial_004",
        "category": "partially_hallucinated",
        "expected_decision": "ABSTAIN",
        "text": "Section 43 imposes civil liability for unauthorized access to computer systems. The compensation can extend up to Rs. 5 crores depending on the damage caused.",
        "description": "Correct about civil liability but wrong about compensation cap",
        "difficulty": "medium",
        "accurate_parts": ["Section 43", "civil liability", "unauthorized access"],
        "false_parts": ["Rs. 5 crores cap"]
    },
    {
        "id": "partial_005",
        "category": "partially_hallucinated",
        "expected_decision": "ABSTAIN",
        "text": "Section 69 empowers the government to intercept information for national security. Any person who fails to comply with such orders faces imprisonment up to 10 years.",
        "description": "Correct about interception powers but wrong about imprisonment term (should be 7 years)",
        "difficulty": "hard",
        "accurate_parts": ["Section 69", "government powers", "interception", "national security"],
        "false_parts": ["10 years imprisonment"]
    },

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 3: ACCURATE STATEMENTS (Should be SAFE)
    # ═══════════════════════════════════════════════════════════════
    {
        "id": "accurate_001",
        "category": "accurate",
        "expected_decision": "SAFE",
        "text": "Section 10A of the Information Technology Act, 2000 validates electronic contracts. Contracts cannot be denied enforceability solely on the ground that they are in electronic form.",
        "description": "Completely accurate statement about electronic contract validity",
        "difficulty": "easy",
        "key_facts": ["Section 10A", "electronic contracts", "legal validity"]
    },
    {
        "id": "accurate_002",
        "category": "accurate",
        "expected_decision": "SAFE",
        "text": "Section 67 of the IT Act addresses the publishing or transmitting of obscene material in electronic form and prescribes punishment including imprisonment and fine.",
        "description": "Accurate high-level description of Section 67",
        "difficulty": "easy",
        "key_facts": ["Section 67", "obscene material", "electronic form", "punishment"]
    },
    {
        "id": "accurate_003",
        "category": "accurate",
        "expected_decision": "SAFE",
        "text": "Section 66 of the Information Technology Act deals with computer-related offenses, including hacking. The punishment may extend to imprisonment of up to three years and fine up to five lakh rupees.",
        "description": "Accurate statement with correct punishment details",
        "difficulty": "medium",
        "key_facts": ["Section 66", "hacking", "three years", "five lakh rupees"]
    },
    {
        "id": "accurate_004",
        "category": "accurate",
        "expected_decision": "SAFE",
        "text": "Under the IT Act, Section 43A requires body corporates to implement reasonable security practices for sensitive personal data. Failure to protect such data makes them liable to pay damages by way of compensation.",
        "description": "Accurate description of data protection obligations",
        "difficulty": "medium",
        "key_facts": ["Section 43A", "body corporate", "security practices", "compensation"]
    },
    {
        "id": "accurate_005",
        "category": "accurate",
        "expected_decision": "SAFE",
        "text": "The Information Technology Act provides legal recognition to electronic records and digital signatures under Sections 4 and 5 respectively.",
        "description": "Accurate statement about electronic records and digital signatures",
        "difficulty": "easy",
        "key_facts": ["electronic records", "digital signatures", "Sections 4 and 5"]
    },
    {
        "id": "accurate_006",
        "category": "accurate",
        "expected_decision": "SAFE",
        "text": "Section 79 of the IT Act provides safe harbor protection to intermediaries for third-party content, subject to compliance with due diligence requirements and government takedown notices.",
        "description": "Accurate statement about intermediary liability exemption",
        "difficulty": "hard",
        "key_facts": ["Section 79", "intermediaries", "safe harbor", "due diligence"]
    },

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 4: EDGE CASES & COMPLEX SCENARIOS
    # ═══════════════════════════════════════════════════════════════
    {
        "id": "edge_001",
        "category": "edge_case",
        "expected_decision": "ABSTAIN",
        "text": "The IT Act may impose penalties under multiple sections for a single cyber crime, with Section 66C addressing identity theft and Section 66D covering cheating by personation.",
        "description": "Multi-section reference with accurate but vague language",
        "difficulty": "hard",
        "note": "Vague phrasing ('may impose') makes verification difficult"
    },
    {
        "id": "edge_002",
        "category": "edge_case",
        "expected_decision": "SAFE",
        "text": "Section 67B, which dealt with child pornography, was repealed by the Protection of Children from Sexual Offences Act (POCSO) in 2012.",
        "description": "Accurate statement about repealed section",
        "difficulty": "hard",
        "note": "Tests system's knowledge of amendments and repeals"
    },
    {
        "id": "edge_003",
        "category": "edge_case",
        "expected_decision": "SAFE",
        "text": "Section 66A of the IT Act, which criminalized offensive messages, was struck down by the Supreme Court in Shreya Singhal v. Union of India as unconstitutional.",
        "description": "Accurate statement about invalidated provision",
        "difficulty": "hard",
        "note": "Tests knowledge of case law and constitutional validity"
    },
    {
        "id": "edge_004",
        "category": "edge_case",
        "expected_decision": "ABSTAIN",
        "text": "Sections 43, 66, and 67 collectively address civil liability, hacking, and obscene content respectively under the IT Act framework.",
        "description": "Multiple correct references in single sentence",
        "difficulty": "medium",
        "note": "Tests handling of multi-claim accurate statements"
    },
    {
        "id": "edge_005",
        "category": "edge_case",
        "expected_decision": "FLAGGED",
        "text": "Section 43 creates criminal liability while Section 66 creates civil liability under the IT Act.",
        "description": "Inverted claim - completely backwards",
        "difficulty": "easy",
        "note": "Tests detection of reversed/inverted facts"
    },
]

# Test case statistics
def get_test_statistics():
    """Calculate statistics about the test suite."""
    total = len(COMPREHENSIVE_TEST_CASES)
    by_category = {}
    by_difficulty = {}
    by_expected = {}
    
    for case in COMPREHENSIVE_TEST_CASES:
        category = case.get('category', 'unknown')
        difficulty = case.get('difficulty', 'unknown')
        expected = case.get('expected_decision', 'unknown')
        
        by_category[category] = by_category.get(category, 0) + 1
        by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1
        by_expected[expected] = by_expected.get(expected, 0) + 1
    
    return {
        'total_cases': total,
        'by_category': by_category,
        'by_difficulty': by_difficulty,
        'by_expected_decision': by_expected
    }

if __name__ == "__main__":
    stats = get_test_statistics()
    print("=" * 70)
    print("COMPREHENSIVE TEST SUITE STATISTICS")
    print("=" * 70)
    print(f"\nTotal Test Cases: {stats['total_cases']}")
    
    print("\n📊 By Category:")
    for category, count in sorted(stats['by_category'].items()):
        percentage = (count / stats['total_cases']) * 100
        print(f"  {category:25s}: {count:2d} ({percentage:5.1f}%)")
    
    print("\n🎯 By Difficulty:")
    for difficulty, count in sorted(stats['by_difficulty'].items()):
        percentage = (count / stats['total_cases']) * 100
        print(f"  {difficulty:25s}: {count:2d} ({percentage:5.1f}%)")
    
    print("\n✅ By Expected Decision:")
    for decision, count in sorted(stats['by_expected_decision'].items()):
        percentage = (count / stats['total_cases']) * 100
        print(f"  {decision:25s}: {count:2d} ({percentage:5.1f}%)")
    
    print("\n" + "=" * 70)
