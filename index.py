import os
import requests
from pathlib import Path
import lancedb
from lancedb.pydantic import LanceModel, Vector
from typing import List, Dict

# Configuration
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "nomic-embed-text:latest"
DB_PATH = "code_embeddings.lance"

class CodeChunk(LanceModel):
    filename: str
    text: str
    vector: Vector(768)  # nomic-embed-text dimension

def get_embedding(text: str) -> List[float]:
    """Get embeddings from Ollama API."""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": MODEL_NAME, "prompt": text}
    )
    return response.json()["embedding"]

def should_ignore(path: str) -> bool:
    """Check if the path should be ignored."""
    ignore_patterns = [
        'venv',
        '__pycache__',
        '.git',
        '.env',
        'code_embeddings.lance',
        'node_modules'
    ]
    return any(pattern in path for pattern in ignore_patterns)

def chunk_file(file_path: str, max_chunk_size: int = 1000) -> List[Dict]:
    """Simple chunking strategy that splits files into chunks of approximately equal size."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping binary file: {file_path}")
        return []
    
    # Split content into lines
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line)
        if current_size + line_size > max_chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return [{"filename": file_path, "text": chunk} for chunk in chunks]

def index_codebase(root_dir: str):
    """Index all code files in the given directory."""
    print(f"Indexing codebase in {root_dir}...")
    
    # Connect to LanceDB
    db = lancedb.connect(DB_PATH)
    
    # Create table if it doesn't exist
    if "code_chunks" not in db.table_names():
        table = db.create_table("code_chunks", schema=CodeChunk, mode="create")
        print("Created new database table.")
    else:
        table = db.open_table("code_chunks")
        print("Using existing database table.")
    
    # Walk through the directory
    total_files = 0
    total_chunks = 0
    
    for root, dirs, files in os.walk(root_dir):
        # Skip ignored directories
        if should_ignore(root):
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip ignored files
            if should_ignore(file_path):
                continue
                
            # Only process text files
            if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.md', '.txt', '.json', '.yaml', '.yml')):
                print(f"Processing {file_path}")
                total_files += 1
                
                # Get chunks for the file
                chunks = chunk_file(file_path)
                
                # Generate embeddings and add to database
                for chunk in chunks:
                    embedding = get_embedding(chunk["text"])
                    table.add([{
                        "filename": chunk["filename"],
                        "text": chunk["text"],
                        "vector": embedding
                    }])
                    total_chunks += 1
                    print(f"Added chunk {total_chunks} from {file_path}")
    
    print(f"\nIndexing complete!")
    print(f"Total files processed: {total_files}")
    print(f"Total chunks created: {total_chunks}")

if __name__ == "__main__":
    # Index the current directory
    index_codebase(".") 