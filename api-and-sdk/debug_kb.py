#!/usr/bin/env python
"""
Debug Knowledge Base Content and Search
=====================================

Check what's actually in the KB and test search functionality
"""

import sys
from pathlib import Path

# Add paths
_API_SDK_ROOT = Path(__file__).resolve().parent
_DETECTION_ENGINE_ROOT = _API_SDK_ROOT.parent / "detection-engine"
_PROJECT_ROOT = _API_SDK_ROOT.parent
for _p in (_API_SDK_ROOT, _DETECTION_ENGINE_ROOT, _PROJECT_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dotenv import load_dotenv
load_dotenv()

from api.kb.db import SessionLocal
from api.kb.models import StatuteSection, CaseLaw
from api.kb.vector_kb import VectorRetriever
from shared.schemas import Claim, ClaimType

def check_kb_content():
    """Check what's in the KB database"""
    print("🔍 Checking Knowledge Base Content...")
    
    session = SessionLocal()
    try:
        # Check statutes
        statutes = session.query(StatuteSection).all()
        print(f"📚 Total Statutes in DB: {len(statutes)}")
        
        # Check IT Act sections specifically
        it_act_statutes = session.query(StatuteSection).filter(
            StatuteSection.act_name.ilike('%information technology%')
        ).all()
        print(f"⚖️ IT Act Statutes: {len(it_act_statutes)}")
        
        # Show first few IT Act sections
        if it_act_statutes:
            print("\n📋 Sample IT Act Sections in KB:")
            for i, statute in enumerate(it_act_statutes[:5]):
                print(f"  {i+1}. Section {statute.section_number}: {statute.section_text[:60]}...")
        else:
            print("❌ No IT Act sections found in KB!")
        
        # Check case law
        cases = session.query(CaseLaw).all()
        print(f"\n📖 Total Cases in DB: {len(cases)}")
        
        if cases:
            print("\n📋 Sample Cases in KB:")
            for i, case in enumerate(cases[:3]):
                print(f"  {i+1}. {case.case_name[:50]}...")
                
    except Exception as e:
        print(f"❌ Error accessing DB: {e}")
    finally:
        session.close()

def test_vector_search():
    """Test vector search functionality"""
    print("\n🔎 Testing Vector Search...")
    
    try:
        retriever = VectorRetriever()
        
        # Test searches for IT Act sections
        test_queries = [
            "Section 43 Information Technology Act",
            "Section 66 cyber terrorism",
            "Section 67 obscene material",
            "Section 10A electronic contracts",
            "computer access without permission"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            try:
                results = retriever.retrieve_with_metadata(query, top_k=3)
                
                if results:
                    print(f"   Found {len(results)} results:")
                    for i, result in enumerate(results[:2]):
                        print(f"   {i+1}. Score: {result.score:.3f}")
                        print(f"      Source: {result.source}")
                        print(f"      Text: {result.text[:80]}...")
                else:
                    print("   ❌ No results found")
                    
            except Exception as e:
                print(f"   ❌ Search error: {e}")
                
    except Exception as e:
        print(f"❌ Vector search setup error: {e}")

def test_claim_lookup():
    """Test the actual claim lookup that the system uses"""
    print("\n🎯 Testing Claim Lookup (as used by system)...")
    
    try:
        from stages.kb_lookup import kb_lookup
        
        # Create test claims
        test_claims = [
            Claim(
                id="test_1",
                text="Section 43 of the Information Technology Act provides for civil liability",
                type=ClaimType.SECTION_REF,
                span=[0, 50]
            ),
            Claim(
                id="test_2", 
                text="Section 67 punishes obscene material in electronic form",
                type=ClaimType.SECTION_REF,
                span=[0, 40]
            ),
            Claim(
                id="test_3",
                text="K.S. Puttaswamy established privacy rights",
                type=ClaimType.HOLDING,
                span=[0, 30]
            )
        ]
        
        for claim in test_claims:
            print(f"\n🔍 Testing claim: '{claim.text}'")
            try:
                result = kb_lookup(claim)
                
                print(f"   Hit: {result.hit}")
                print(f"   Best Score: {result.best_score:.3f}")
                print(f"   Passages Found: {len(result.passages)}")
                
                if result.passages:
                    best = result.passages[0]
                    print(f"   Best Match: {best.source}")
                    print(f"   Text: {best.text[:100]}...")
                else:
                    print("   ❌ No passages found")
                    
            except Exception as e:
                print(f"   ❌ Lookup error: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Claim lookup setup error: {e}")
        import traceback
        traceback.print_exc()

def check_index_files():
    """Check if FAISS index files exist"""
    print("\n📂 Checking Index Files...")
    
    index_dir = Path("api/kb/index")
    if index_dir.exists():
        files = list(index_dir.glob("*"))
        print(f"   Index directory exists with {len(files)} files:")
        for file in files:
            size = file.stat().st_size if file.is_file() else 0
            print(f"   - {file.name} ({size} bytes)")
    else:
        print("   ❌ Index directory not found!")
    
    # Check for specific IT Act index
    it_act_index = index_dir / "it_act.faiss"
    it_act_metadata = index_dir / "it_act_metadata.json"
    
    print(f"   IT Act FAISS index exists: {it_act_index.exists()}")
    print(f"   IT Act metadata exists: {it_act_metadata.exists()}")

if __name__ == "__main__":
    print("🚀 Knowledge Base Debug Analysis")
    print("=" * 50)
    
    check_index_files()
    check_kb_content() 
    test_vector_search()
    test_claim_lookup()