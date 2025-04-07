import lancedb
import os

def inspect_database():
    """Inspect the contents of the LanceDB database."""
    db_path = "code_embeddings.lance"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
        
    try:
        db = lancedb.connect(db_path)
        if "code_chunks" not in db.table_names():
            print("❌ Table 'code_chunks' not found in database")
            return
            
        table = db.open_table("code_chunks")
        
        # Get total count
        total_rows = table.count_rows()
        print(f"\n=== Database Statistics ===")
        print(f"Total chunks: {total_rows}")
        
        # Get unique filenames
        filenames = table.to_pandas()["filename"].unique()
        print(f"\n=== Files in Database ===")
        for filename in filenames:
            count = table.to_pandas()["filename"].value_counts()[filename]
            print(f"- {filename}: {count} chunks")
            
        # Show sample of content
        print(f"\n=== Sample Content ===")
        sample = table.to_pandas().iloc[0]
        print(f"Sample from {sample['filename']}:")
        print(f"Content preview: {sample['text'][:200]}...")
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_database() 