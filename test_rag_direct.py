import rag
import time

def test_direct():
    print("Testing rag.py directly...")
    
    # 1. Test Embedding
    print("1. Testing get_embedding...")
    text = "This is a test sentence about Python."
    emb = rag.get_embedding(text)
    if emb:
        print(f"   Success! Embedding length: {len(emb)}")
    else:
        print("   Failed to get embedding.")
        return

    # 2. Test Indexing
    print("2. Testing index_content...")
    courses_data = [
        {
            "id": 1,
            "title": "Python for Beginners",
            "description": "Learn Python from scratch.",
            "modules": [
                {"id": 101, "title": "Intro to Python", "contentLink": "video.mp4"}
            ]
        }
    ]
    rag.index_content(courses_data)
    print(f"   Index size: {len(rag.VECTOR_STORE)}")

    # 3. Test Retrieval
    print("3. Testing retrieve...")
    query = "How do I learn Python?"
    results = rag.retrieve(query)
    print(f"   Retrieved {len(results)} results.")
    for chunk in results:
        print(f"   - {chunk['text'][:50]}... (Score: {chunk.get('score', 'N/A')})")

    # 4. Test Generation
    print("4. Testing generate_response...")
    response = rag.generate_response(query, results)
    print(f"   Response: {response}")

if __name__ == "__main__":
    test_direct()
