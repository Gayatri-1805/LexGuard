"""
Stage 2: Ground

Person A - Detection Engine
Retrieves relevant legal knowledge (statutes, case law, legal concepts)
from the knowledge base (Person B's kb_interface) to ground each sub-claim.

Depends on: Person B completing kb/kb_interface.py and kb/postgres_kb.py

Input: FilteredClaim with entities
Output: GroundedClaim with retrieved knowledge context per sub-claim
"""
