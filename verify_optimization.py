import sys
import os
import json

# Add current directory to path
sys.path.append(os.getcwd())

import rag

def test_persistence():
    print("Testing RAG persistence...")
    
    # Define test data
    test_courses = [
        {"id": 1, "title": "Test Title", "description": "Test Description", "modules": []}
    ]
    
    # 1. Index and Save
    print("Indexing content...")
    rag.index_content(test_courses)
    
    # 2. Check if file exists
    if os.path.exists(rag.INDEX_FILE):
        print(f"Success: {rag.INDEX_FILE} created.")
    else:
        print("Error: Index file not created.")
        return False
        
    # 3. Simulate new process/import by clearing in-memory store
    print("Clearing in-memory store and loading from disk...")
    rag.VECTOR_STORE = None
    
    # 4. Retrieve (should trigger load_index)
    results = rag.retrieve("Test")
    if results and "Test Title" in results[0]:
        print("Success: Data correctly retrieved from disk cache.")
    else:
        print(f"Error: Retrieval failed. Results: {results}")
        return False
        
    return True

if __name__ == "__main__":
    if test_persistence():
        print("\nPERSISTENCE TEST PASSED!")
    else:
        print("\nPERSISTENCE TEST FAILED!")
        sys.exit(1)
