"""
Quick test to verify the keyword search functionality.
"""
from src.aixplain_client import AIXplainClient
from src.models import Document, DocumentType
from src.config import config

print("Testing keyword-based search...")

# Initialize client
try:
    client = AIXplainClient()
    print("✅ Client initialized")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Create a test document
doc = Document(
    document_id="test_001",
    name="Test Document",
    document_type=DocumentType.TEXT,
    content="""
    نظام الخدمة المدنية يحدد شروط التوظيف.
    يجب التحقق من صحة المستندات قبل الموافقة.
    تصرف الرواتب في نهاية كل شهر.
    الفواتير يجب أن تكون موثقة ومعتمدة.
    العقود الحكومية تخضع لنظام المنافسات.
    """
)

# Index document
print("\n📊 Indexing document...")
try:
    result = client.create_vector_index([doc], use_chunking=False)
    print(f"✅ Indexed: {result['num_chunks']} chunks")
    print(f"   Storage: {result['storage_type']}")
    print(f"   Index ID: {result['index_id']}")
except Exception as e:
    print(f"❌ Indexing failed: {e}")
    exit(1)

# Test search
print("\n🔍 Testing search queries...")

queries = [
    "ما هي شروط التوظيف؟",
    "كيف تصرف الرواتب؟",
    "ما هي متطلبات الفواتير؟"
]

for i, query in enumerate(queries, 1):
    print(f"\nQuery {i}: {query}")
    try:
        results = client.semantic_search(query, top_k=2)
        if results:
            print(f"✅ Found {len(results)} results:")
            for r in results:
                print(f"   - Score: {r['score']:.3f}")
                print(f"     Text: {r['text'][:100]}...")
                print(f"     Method: {r['retrieval_method']}")
        else:
            print("⚠️  No results found")
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

print("\n✅ Test complete!")
