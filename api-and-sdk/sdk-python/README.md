# Legal Hallucination Detection SDK (Python)

Client library for the legal hallucination detection API.

## Installation

```bash
pip install -e .
```

## Usage

```python
from legal_hallucination_sdk import HallucinationDetectorClient

client = HallucinationDetectorClient(base_url="http://localhost:8000/api")

# Check for hallucinations
response = client.check(
    text="Section 43A requires compensation for data breach.",
    context="Legal analysis"
)

print(response["decision"])      # SAFE, FLAGGED, or ABSTAIN
print(response["trust_index"])   # 0-1 confidence score
print(response["claims"])        # Atomic claims extracted
print(response["verdicts"])      # Analysis results per claim

# Get analytics summary
summary = client.get_summary(days=30)
print(f"Avg trust: {summary['avg_trust_index']}")
print(f"Total flagged: {summary['checks_flagged']}")

# Get flagged checks for review
flagged = client.get_flagged(limit=10)
for check in flagged["flagged_checks"]:
    print(f"{check['request_id']}: {check['decision']} (trust: {check['trust_index']})")
```

## Error Handling

```python
from legal_hallucination_sdk import DetectorAPIError

try:
    response = client.check(text="...")
except DetectorAPIError as e:
    print(f"API Error {e.status_code}: {e.detail}")
```
