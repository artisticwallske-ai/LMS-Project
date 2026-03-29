from typing import List, Dict, Optional
from app.core.database import supabase_client

class KnowledgeGraphService:
    def __init__(self):
        self.client = supabase_client

    def get_prerequisites(self, topic: str) -> List[Dict]:
        """
        Get prerequisites for a given topic.
        Returns a list of topic dictionaries with details.
        """
        try:
            # Simple exact match for now. 
            # In production, we'd use fuzzy matching or vector search to map the input topic to the KG node.
            response = self.client.table("topic_relationships")\
                .select("*")\
                .eq("target_topic", topic)\
                .eq("relationship_type", "prerequisite")\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"Error fetching prerequisites for {topic}: {e}")
            return []

    def get_related_topics(self, topic: str) -> List[Dict]:
        """
        Get related topics (not strictly prerequisites).
        """
        try:
            response = self.client.table("topic_relationships")\
                .select("*")\
                .eq("source_topic", topic)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching related topics for {topic}: {e}")
            return []

knowledge_graph_service = KnowledgeGraphService()
