import os
import sys
import requests
import lancedb
import time
from pathlib import Path

def test_database():
    """Test if the database exists and contains data."""
    print("\n=== Testing Database ===")
    
    db_path = "code_embeddings.lance"
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        db = lancedb.connect(db_path)
        if "code_chunks" not in db.table_names():
            print("❌ Database table 'code_chunks' not found!")
            return False
        
        table = db.open_table("code_chunks")
        count = table.count_rows()
        print(f"✅ Database exists and contains {count} chunks")
        return True
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False

def test_server():
    """Test if the server is running and can respond to queries."""
    print("\n=== Testing Server ===")
    
    # Try to connect to the server
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ Server is running (FastAPI docs accessible)")
        else:
            print(f"❌ Server returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False
    
    # Test the retrieve endpoint
    try:
        response = requests.post(
            "http://localhost:8000/retrieve",
            json={"query": "test query", "fullInput": "test input"}
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Server responded with {len(results)} results")
            if results:
                print("Sample result:")
                print(f"  File: {results[0].get('name', 'N/A')}")
                print(f"  Content: {results[0].get('content', 'N/A')[:100]}...")
            return True
        else:
            print(f"❌ Server returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing retrieve endpoint: {e}")
        return False

def main():
    """Run all tests and provide a summary."""
    print("=== Testing Code Search System ===")
    
    db_ok = test_database()
    server_ok = test_server()
    
    print("\n=== Summary ===")
    if db_ok and server_ok:
        print("✅ All tests passed! Your system is working correctly.")
        print("You can now use the Continue extension with your custom RAG system.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        if not db_ok:
            print("  - Try running 'python index.py' to rebuild the database")
        if not server_ok:
            print("  - Try running 'python server.py' to start the server")

if __name__ == "__main__":
    main() 