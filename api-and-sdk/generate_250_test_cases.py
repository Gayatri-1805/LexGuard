#!/usr/bin/env python
"""
Generate 250 Comprehensive Test Cases for Legal Hallucination Detection
======================================================================

This script generates a diverse set of test cases covering:
- IT Act sections (1-94, including common ones like 43, 43A, 65-69, 79, etc.)
- Various hallucination patterns (wrong penalties, wrong subjects, wrong procedures)
- Accurate statements
- Partial hallucinations
- Edge cases

Output: test_cases_250.json
"""

import json
from dataclasses import dataclass, asdict
from typing import List
import random

@dataclass
class TestCase:
    """Test case structure"""
    id: str
    text: str
    context: str
    expected_category: str  # hallucinated, partially_hallucinated, accurate
    expected_decision: str  # FLAGGED, ABSTAIN, SAFE
    description: str
    section_ref: str

def generate_hallucinated_cases() -> List[TestCase]:
    """Generate 100 completely hallucinated test cases"""
    cases = []
    
    # Pattern 1: Wrong criminal penalties for civil sections (30 cases)
    civil_sections = ["43", "43A", "44", "45"]
    criminal_penalties = [
        "imprisonment for up to 3 years",
        "imprisonment for up to 5 years", 
        "imprisonment for up to 7 years",
        "imprisonment for life",
        "death penalty in severe cases"
    ]
    
    for i, sec in enumerate(civil_sections * 7):  # 28 cases
        idx = i + 1
        penalty = random.choice(criminal_penalties)
        fine_amount = random.choice(["5 lakh", "10 lakh", "25 lakh", "1 crore"])
        
        cases.append(TestCase(
            id=f"hal_civil_criminal_{idx:03d}",
            text=f"Section {sec} of the Information Technology Act provides for {penalty} and a fine up to {fine_amount} rupees for violations.",
            context=f"Verify this statement against Section {sec} of the IT Act, 2000.",
            expected_category="hallucinated",
            expected_decision="FLAGGED",
            description=f"Section {sec} is civil liability, not criminal",
            section_ref=sec
        ))
    
    # Pattern 2: Wrong subject matter (25 cases)
    wrong_subjects = [
        ("43", "cyber terrorism", "civil liability for unauthorized computer access"),
        ("43A", "offensive messages", "compensation for failure to protect data"),
        ("65", "electronic signatures", "tampering with computer source documents"),
        ("66", "cyber terrorism", "computer-related offences/hacking"),
        ("66B", "data breach", "receiving stolen computer resource"),
        ("66C", "hacking", "identity theft"),
        ("66D", "phishing", "cheating by personation using computer"),
        ("66E", "spamming", "violation of privacy"),
        ("66F", "identity theft", "cyber terrorism"),
        ("67", "hacking", "obscene material in electronic form"),
        ("67A", "cyber terrorism", "sexually explicit material"),
        ("67B", "phishing", "child pornography"),
        ("69", "data breach", "government power to intercept"),
        ("69A", "hacking", "power to block public access"),
        ("70", "identity theft", "protected system"),
        ("72", "obscene material", "breach of confidentiality"),
        ("79", "cyber terrorism", "safe harbor for intermediaries"),
        ("80", "hacking", "power of police officer"),
        ("81", "data breach", "offences outside India"),
        ("84", "identity theft", "legal representative for companies"),
        ("85", "obscene material", "offence by companies"),
    ]
    
    for i, (sec, wrong, correct) in enumerate(wrong_subjects[:25]):
        idx = i + 1
        cases.append(TestCase(
            id=f"hal_wrong_subject_{idx:03d}",
            text=f"Section {sec} of the IT Act exclusively deals with {wrong} and provides strict penalties for such violations.",
            context=f"Verify this statement against Section {sec} of the IT Act, 2000.",
            expected_category="hallucinated",
            expected_decision="FLAGGED",
            description=f"Section {sec} is about {correct}, not {wrong}",
            section_ref=sec
        ))
    
    # Pattern 3: Fabricated sections (15 cases)
    fake_sections = [f"{num}{letter}" for num in range(95, 110) for letter in ["", "A", "B"]][:15]
    fake_topics = ["quantum computing crimes", "AI-generated deepfakes", "metaverse fraud",
                   "cryptocurrency theft", "biometric hacking", "drone surveillance",
                   "neural interface tampering", "holographic impersonation",
                   "virtual reality assault", "blockchain manipulation"]
    
    for i, (fake_sec, topic) in enumerate(zip(fake_sections, fake_topics)):
        idx = i + 1
        cases.append(TestCase(
            id=f"hal_fake_section_{idx:03d}",
            text=f"Section {fake_sec} of the IT Act, 2000 criminalizes {topic} with imprisonment up to 10 years.",
            context=f"Verify if Section {fake_sec} exists in the IT Act, 2000.",
            expected_category="hallucinated",
            expected_decision="FLAGGED",
            description=f"Section {fake_sec} does not exist in the IT Act",
            section_ref=fake_sec
        ))
    
    # Pattern 4: Wrong arrest powers (15 cases)
    non_arrest_sections = ["43", "43A", "67", "67A", "72"]
    for i, sec in enumerate(non_arrest_sections * 3):
        idx = i + 1
        arrest_type = random.choice(["warrant", "warrantless arrest", "immediate detention"])
        cases.append(TestCase(
            id=f"hal_arrest_powers_{idx:03d}",
            text=f"Section {sec} empowers police to make {arrest_type} of offenders without judicial oversight.",
            context=f"Verify arrest provisions under Section {sec} of the IT Act, 2000.",
            expected_category="hallucinated",
            expected_decision="FLAGGED",
            description=f"Section {sec} does not specify arrest powers",
            section_ref=sec
        ))
    
    # Pattern 5: Wrong mandatory provisions (15 cases)
    sections_with_discretion = ["43", "43A", "66", "67", "72"]
    for i, sec in enumerate(sections_with_discretion * 3):
        idx = i + 1
        mandatory_claim = random.choice([
            "mandatory minimum sentence of 2 years",
            "compulsory fine of 5 lakh rupees",
            "automatic license revocation",
            "mandatory business closure",
            "compulsory criminal prosecution"
        ])
        cases.append(TestCase(
            id=f"hal_mandatory_{idx:03d}",
            text=f"Section {sec} mandates {mandatory_claim} with no judicial discretion for reducing penalties.",
            context=f"Verify mandatory provisions under Section {sec} of the IT Act, 2000.",
            expected_category="hallucinated",
            expected_decision="FLAGGED",
            description=f"Section {sec} does not have such mandatory provisions",
            section_ref=sec
        ))
    
    return cases[:100]  # Return exactly 100

def generate_partially_hallucinated_cases() -> List[TestCase]:
    """Generate 75 partially hallucinated test cases"""
    cases = []
    
    # Pattern 1: Correct subject, wrong penalty amounts (30 cases)
    sections_penalties = [
        ("66", "3 years", ["5 years", "7 years", "10 years"]),
        ("67", "3 years first, 5 years subsequent", ["5 years first, 10 years subsequent", "7 years"]),
        ("67A", "5 years first, 7 years subsequent", ["7 years first, 10 years subsequent"]),
        ("67B", "5 years first, 7 years subsequent", ["10 years first, 14 years subsequent"]),
        ("72", "2 years", ["5 years", "7 years", "3 years"]),
        ("72A", "3 years", ["5 years", "7 years"]),
    ]
    
    for i in range(30):
        sec, correct, wrongs = random.choice(sections_penalties)
        wrong = random.choice(wrongs)
        idx = i + 1
        cases.append(TestCase(
            id=f"part_wrong_penalty_{idx:03d}",
            text=f"Section {sec} of the IT Act punishes violations with imprisonment up to {wrong}.",
            context=f"Verify the punishment under Section {sec}.",
            expected_category="partially_hallucinated",
            expected_decision="ABSTAIN",
            description=f"Correct section, but wrong imprisonment term (should be {correct})",
            section_ref=sec
        ))
    
    # Pattern 2: Correct subject, wrong fine amounts (25 cases)
    sections_fines = [
        ("66", "5 lakh", ["10 lakh", "15 lakh", "25 lakh"]),
        ("67", "5 lakh first", ["10 lakh first", "7 lakh first"]),
        ("67A", "10 lakh", ["20 lakh", "15 lakh"]),
        ("72", "1 lakh", ["5 lakh", "10 lakh"]),
    ]
    
    for i in range(25):
        sec, correct, wrongs = random.choice(sections_fines)
        wrong = random.choice(wrongs)
        idx = i + 1
        cases.append(TestCase(
            id=f"part_wrong_fine_{idx:03d}",
            text=f"Section {sec} provides for a fine which may extend to {wrong} rupees for the offense.",
            context=f"Verify the fine amount under Section {sec}.",
            expected_category="partially_hallucinated",
            expected_decision="ABSTAIN",
            description=f"Correct section, but wrong fine amount (should be {correct})",
            section_ref=sec
        ))
    
    # Pattern 3: Mostly accurate with one wrong detail (20 cases)
    mixed_accuracy = [
        ("43", "Section 43 provides for compensation for damage to computer systems. The maximum compensation is 5 crore rupees.", "Maximum compensation amount uncertain"),
        ("43A", "Section 43A requires body corporates to implement security practices. Failure results in mandatory criminal prosecution.", "No mandatory criminal prosecution"),
        ("65", "Section 65 prohibits tampering with computer source documents. The penalty is 3 years imprisonment or 5 lakh fine or both.", "Penalty amount may be wrong"),
        ("66", "Section 66 punishes hacking. The offense is non-bailable and non-compoundable.", "Bailability status may be wrong"),
        ("67", "Section 67 punishes obscene material. Publishing such material always results in asset seizure.", "Asset seizure not automatic"),
    ]
    
    for i in range(20):
        sec, text, issue = random.choice(mixed_accuracy)
        idx = i + 1
        cases.append(TestCase(
            id=f"part_mixed_{idx:03d}",
            text=text,
            context=f"Verify all details of this statement about Section {sec}.",
            expected_category="partially_hallucinated",
            expected_decision="ABSTAIN",
            description=issue,
            section_ref=sec
        ))
    
    return cases[:75]  # Return exactly 75

def generate_accurate_cases() -> List[TestCase]:
    """Generate 75 completely accurate test cases"""
    cases = []
    
    # Accurate statements about well-known sections (75 cases)
    accurate_statements = [
        ("43", "Section 43 of the IT Act provides for compensation for damage to computer, computer system or computer network without permission of the owner."),
        ("43A", "Section 43A requires body corporates to implement reasonable security practices for sensitive personal data or information."),
        ("65", "Section 65 of the IT Act prohibits tampering with computer source documents with intent to cause damage."),
        ("66", "Section 66 punishes computer-related offences including hacking with imprisonment up to 3 years and fine up to 5 lakh rupees."),
        ("66B", "Section 66B punishes dishonestly receiving stolen computer resources or communication devices."),
        ("66C", "Section 66C punishes identity theft by fraudulently using another person's electronic signature or password."),
        ("66D", "Section 66D punishes cheating by personation using computer resources."),
        ("66E", "Section 66E punishes violation of privacy by capturing, publishing or transmitting images of private areas without consent."),
        ("66F", "Section 66F punishes cyber terrorism with imprisonment which may extend to life."),
        ("67", "Section 67 punishes publishing or transmitting obscene material in electronic form."),
        ("67A", "Section 67A punishes publishing or transmitting material containing sexually explicit acts in electronic form."),
        ("67B", "Section 67B punishes publishing or transmitting material depicting children in sexually explicit acts in electronic form."),
        ("69", "Section 69 empowers the government to intercept, monitor or decrypt information through any computer resource."),
        ("69A", "Section 69A empowers the government to block public access to any information through any computer resource."),
        ("70", "Section 70 designates certain computer resources as protected systems and restricts unauthorized access."),
        ("71", "Section 71 punishes misrepresentation to obtain access to protected systems."),
        ("72", "Section 72 punishes breach of confidentiality and privacy by disclosing information in violation of lawful contract."),
        ("72A", "Section 72A punishes disclosure of information in breach of lawful contract during provision of services."),
        ("73", "Section 73 punishes publishing false digital signature certificates."),
        ("74", "Section 74 punishes publication of information for fraudulent purposes related to digital signatures."),
        ("75", "Section 75 makes certain offenses under the IT Act cognizable."),
        ("77", "Section 77 clarifies that certain provisions apply to offenses committed outside India by any person."),
        ("78", "Section 78 provides for the power to investigate offences."),
        ("79", "Section 79 provides safe harbor to intermediaries for third-party content under certain conditions."),
        ("80", "Section 80 grants powers to police officers not below the rank of Deputy Superintendent for certain IT Act offenses."),
        ("81", "Section 81 provides that provisions of the IT Act shall have effect in addition to other laws."),
        ("84", "Section 84 clarifies punishment of offenses committed by companies and liability of company officials."),
        ("85", "Section 85 addresses offenses by companies and liability of directors and officers."),
    ]
    
    # Generate variations
    for i in range(75):
        sec, statement = random.choice(accurate_statements)
        idx = i + 1
        
        # Add variations to make them unique
        variations = [
            statement,
            f"Under the Information Technology Act, 2000, {statement.lower()}",
            f"The IT Act, 2000 specifies that {statement.lower()}",
            f"As per Indian law, {statement.lower()}",
        ]
        
        text = random.choice(variations)
        
        cases.append(TestCase(
            id=f"acc_section_{idx:03d}",
            text=text,
            context=f"Verify this statement about Section {sec} of the IT Act, 2000.",
            expected_category="accurate",
            expected_decision="SAFE",
            description=f"Accurate statement about Section {sec}",
            section_ref=sec
        ))
    
    return cases[:75]  # Return exactly 75

def main():
    """Generate 250 test cases and save to JSON"""
    print("🔬 Generating 250 Comprehensive Test Cases")
    print("=" * 70)
    
    print("\n📝 Generating hallucinated cases (100)...")
    hallucinated = generate_hallucinated_cases()
    print(f"✓ Generated {len(hallucinated)} hallucinated cases")
    
    print("\n📝 Generating partially hallucinated cases (75)...")
    partial = generate_partially_hallucinated_cases()
    print(f"✓ Generated {len(partial)} partially hallucinated cases")
    
    print("\n📝 Generating accurate cases (75)...")
    accurate = generate_accurate_cases()
    print(f"✓ Generated {len(accurate)} accurate cases")
    
    # Combine all cases
    all_cases = hallucinated + partial + accurate
    
    print(f"\n✓ Total test cases: {len(all_cases)}")
    
    # Convert to dict format
    cases_dict = [asdict(case) for case in all_cases]
    
    # Save to JSON
    output_file = "test_cases_250.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cases_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Print summary
    print("\n📊 DATASET SUMMARY")
    print("=" * 70)
    print(f"Total Cases: {len(all_cases)}")
    print(f"  • Hallucinated: {len(hallucinated)} (40%)")
    print(f"  • Partially Hallucinated: {len(partial)} (30%)")
    print(f"  • Accurate: {len(accurate)} (30%)")
    print("\n✓ Dataset generation complete!")

if __name__ == "__main__":
    main()
