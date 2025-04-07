from fastapi import FastAPI
from pydantic import BaseModel
import lancedb
import requests
from typing import List, Dict
import os
import numpy as np

# Configuration
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "nomic-embed-text:latest"
DB_PATH = "code_embeddings.lance"

app = FastAPI()

class ContextProviderInput(BaseModel):
    query: str
    fullInput: str

def get_embedding(text: str) -> List[float]:
    """Get embeddings from Ollama API."""
    try:
        print(f"\n=== Embedding Request ===")
        print(f"Query text: {text}")
        print(f"Requesting embedding from: {OLLAMA_URL}/api/embeddings")
        print(f"Using model: {MODEL_NAME}")
        
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": MODEL_NAME, "prompt": text}
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code != 200:
            print(f"Error from Ollama API: {response.status_code} - {response.text}")
            return []
        
        result = response.json()
        print(f"Response JSON: {result}")
        
        if "embedding" not in result:
            print(f"Error: No embedding in response: {result}")
            return []
        
        embedding = result["embedding"]
        print(f"Embedding length: {len(embedding)}")
        print(f"First few values: {embedding[:5]}")
        print("=== End Embedding Request ===\n")
            
        return embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return []

@app.post("/retrieve")
async def retrieve_context(item: ContextProviderInput):
    print("\n=== Request Details ===")
    print(f"Query: {item.query}")
    print(f"Full Input: {item.fullInput}")
    
    # Use fullInput as fallback if query is empty
    search_text = item.query if item.query and item.query.strip() else item.fullInput
    
    # Input validation
    if not search_text or search_text.strip() == "":
        print("Empty query and fullInput received in request")
        return []
    
    # Connect to LanceDB
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table("code_chunks")
        
        # Get embedding for the query
        query_embedding = get_embedding(search_text)
        
        if not query_embedding:
            print("Failed to get embedding for query")
            return []
        
        # Convert to numpy array for LanceDB
        query_embedding_np = np.array(query_embedding)
        
        # Search for similar chunks
        results = table.search(query_embedding_np).limit(5).to_list()
        
        # Format results for Continue
        context_items = []
        for result in results:
            # Clean and format the content
            content = result["text"].strip()
            if not content:
                continue
                
            context_items.append({
                "name": result["filename"],
                "description": f"Similarity: {result['_distance']:.2f}",
                "content": content
            })
        
        print("\n=== Response Details ===")
        print(f"Number of results: {len(context_items)}")
        for idx, item in enumerate(context_items, 1):
            print(f"\nResult {idx}:")
            print(f"Name: {item['name']}")
            print(f"Description: {item['description']}")
            print(f"Content preview: {item['content'][:100]}...")
        
        return context_items
    except Exception as e:
        print(f"Error in retrieve_context: {e}")
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 