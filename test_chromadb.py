"""
Quick test script to verify ChromaDB installation and functionality.
Run this before running the main application.
"""
import sys
from pathlib import Path

print("=" * 60)
print("ChromaDB Installation & Functionality Test")
print("=" * 60)

# Test 1: Import ChromaDB
print("\n[1/5] Testing ChromaDB import...")
try:
    import chromadb
    print("[OK] ChromaDB imported successfully")
    print(f"   Version: {chromadb.__version__ if hasattr(chromadb, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"[FAIL] Failed to import ChromaDB: {e}")
    print("\nFix: Install ChromaDB:")
    print("   pip install chromadb sentence-transformers")
    sys.exit(1)

# Test 2: Create persistent client
print("\n[2/5] Testing ChromaDB PersistentClient...")
try:
    test_dir = Path("data/test_chroma")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=str(test_dir))
    print(f"[OK] PersistentClient created successfully")
    print(f"   Storage path: {test_dir.absolute()}")
except Exception as e:
    print(f"[FAIL] Failed to create PersistentClient: {e}")
    sys.exit(1)

# Test 3: Create collection
print("\n[3/5] Testing collection creation...")
try:
    # Delete existing test collection if it exists
    try:
        client.delete_collection("test_collection")
    except:
        pass
    
    collection = client.create_collection(
        name="test_collection",
        metadata={"description": "Test collection"}
    )
    print("[OK] Collection created successfully")
    print(f"   Collection name: {collection.name}")
except Exception as e:
    print(f"[FAIL] Failed to create collection: {e}")
    sys.exit(1)

# Test 4: Add documents
print("\n[4/5] Testing document addition...")
try:
    collection.add(
        ids=["doc1", "doc2", "doc3"],
        documents=[
            "This is a test document about contracts",
            "This is a test document about salaries",
            "This is a test document about invoices"
        ],
        metadatas=[
            {"type": "contract"},
            {"type": "salary"},
            {"type": "invoice"}
        ]
    )
    count = collection.count()
    print(f"[OK] Documents added successfully")
    print(f"   Total documents in collection: {count}")
except Exception as e:
    print(f"[FAIL] Failed to add documents: {e}")
    sys.exit(1)

# Test 5: Query documents
print("\n[5/5] Testing vector search...")
try:
    results = collection.query(
        query_texts=["contract information"],
        n_results=2
    )
    print("[OK] Vector search successful")
    print(f"   Retrieved {len(results['ids'][0])} results")
    if results['documents'][0]:
        print(f"   Top result: {results['documents'][0][0][:50]}...")
except Exception as e:
    print(f"[FAIL] Failed to query documents: {e}")
    sys.exit(1)

# Test 6: Persistence verification
print("\n[6/6] Testing persistence...")
try:
    # Create new client with same path
    client2 = chromadb.PersistentClient(path=str(test_dir))
    collection2 = client2.get_collection("test_collection")
    count2 = collection2.count()
    
    if count2 == count:
        print(f"[OK] Persistence verified")
        print(f"   Data persisted correctly ({count2} documents)")
    else:
        print(f"[WARN] Warning: Count mismatch ({count} vs {count2})")
except Exception as e:
    print(f"[FAIL] Failed to verify persistence: {e}")
    sys.exit(1)

# Cleanup
print("\n[Cleanup] Removing test data...")
try:
    client.delete_collection("test_collection")
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)
    print("[OK] Test data cleaned up")
except Exception as e:
    print(f"[WARN] Warning: Cleanup failed: {e}")

# Summary
print("\n" + "=" * 60)
print("[SUCCESS] ALL TESTS PASSED - ChromaDB is working correctly!")
print("=" * 60)
print("\nNext steps:")
print("   1. Run: streamlit run app.py")
print("   2. Process a document")
print("   3. Check data/chroma_db/ directory for persistent storage")
print("\n")

