from api.kb.postgres_kb import PostgresKB

kb = PostgresKB()

sections = ['10A', '10a', '67A', '67a', '43', '66', '67']

for sec in sections:
    result = kb.lookup_section(sec, 'Information Technology Act, 2000')
    status = f"✅ Found ({len(result)} chars)" if result else "❌ Not found"
    print(f"Section {sec:4s}: {status}")
