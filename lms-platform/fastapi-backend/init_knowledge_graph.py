import os
import sys
from app.core.database import supabase_client

# Add parent directory to path to allow imports if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_knowledge_graph():
    print("Initializing Knowledge Graph (Topic Relationships)...")
    
    # 1. Create table if not exists
    # Note: Supabase-py doesn't support DDL directly via client in all versions, 
    # but we can try to use a stored procedure or just rely on the user to run SQL.
    # However, since I cannot access the dashboard, I will attempt to use a raw SQL query if possible.
    # If raw SQL is not supported by the client, I will assume the table needs to be created manually 
    # and I will just log the schema.
    
    # Actually, for this environment, let's assume we can't run DDL via the client easily 
    # without a specific rpc function.
    # I'll create a mock setup or check if I can insert into a table that doesn't exist (unlikely).
    
    # Strategy: I'll print the SQL needed. 
    # BUT, the user wants me to IMPLEMENT it. 
    # I'll try to use the `rpc` method if there's a generic `exec_sql` function, 
    # otherwise I'll have to skip the table creation and assume it exists or use a workaround.
    
    # WAIT! I can use the `postgres` connection string if I had it, but I only have the Supabase URL/Key.
    # I'll try to check if the table exists first.
    
    print("Checking if 'topic_relationships' table exists...")
    try:
        response = supabase_client.table("topic_relationships").select("id").limit(1).execute()
        print("Table 'topic_relationships' exists.")
    except Exception as e:
        print(f"Table 'topic_relationships' does not exist or error: {e}")
        print("\n[IMPORTANT] Please execute the following SQL in your Supabase SQL Editor:")
        print("""
        CREATE TABLE IF NOT EXISTS topic_relationships (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            source_topic TEXT NOT NULL,
            target_topic TEXT NOT NULL,
            relationship_type TEXT NOT NULL DEFAULT 'prerequisite', -- 'prerequisite', 'related', 'expansion'
            strength FLOAT DEFAULT 1.0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(source_topic, target_topic, relationship_type)
        );
        
        -- Create index for faster lookups
        CREATE INDEX IF NOT EXISTS idx_topic_relationships_source ON topic_relationships(source_topic);
        CREATE INDEX IF NOT EXISTS idx_topic_relationships_target ON topic_relationships(target_topic);
        """)
        
        # For the purpose of this task, if I can't create the table, 
        # the service will have to handle the error gracefully (e.g. return empty prerequisites).
        return

    # 2. Seed with sample data
    print("Seeding sample data...")
    sample_relationships = [
        {"source_topic": "Multiplication", "target_topic": "Division", "relationship_type": "prerequisite"},
        {"source_topic": "Addition", "target_topic": "Multiplication", "relationship_type": "prerequisite"},
        {"source_topic": "Sentences", "target_topic": "Paragraphs", "relationship_type": "prerequisite"},
        {"source_topic": "Plants", "target_topic": "Photosynthesis", "relationship_type": "prerequisite"},
        {"source_topic": "Measurements", "target_topic": "Area", "relationship_type": "prerequisite"},
    ]
    
    for rel in sample_relationships:
        try:
            supabase_client.table("topic_relationships").upsert(rel, on_conflict="source_topic,target_topic,relationship_type").execute()
            print(f"Upserted relationship: {rel['source_topic']} -> {rel['target_topic']}")
        except Exception as e:
            print(f"Error upserting {rel}: {e}")

if __name__ == "__main__":
    init_knowledge_graph()
