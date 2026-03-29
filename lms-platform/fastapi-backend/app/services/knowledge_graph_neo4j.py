from typing import List, Dict, Optional
from neo4j import GraphDatabase
from app.core.config import settings

class Neo4jKnowledgeGraphService:
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except Exception as e:
            print(f"Warning: Failed to connect to Neo4j: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def get_prerequisites(self, topic: str) -> List[Dict]:
        """
        Get prerequisites for a given topic using Neo4j.
        """
        if not self.driver:
            return []
            
        query = """
        MATCH (p:Topic)-[:PREREQUISITE_OF]->(t:Topic {name: $topic})
        RETURN p.name AS prerequisite, p.description AS description
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, topic=topic)
                return [{"source_topic": record["prerequisite"], "description": record["description"]} for record in result]
        except Exception as e:
            print(f"Neo4j Query Error (get_prerequisites): {e}")
            return []

    def get_related_topics(self, topic: str) -> List[Dict]:
        """
        Get related topics in Neo4j.
        """
        if not self.driver:
            return []
            
        query = """
        MATCH (t:Topic {name: $topic})-[:RELATED_TO]-(r:Topic)
        RETURN r.name AS related, r.description AS description
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, topic=topic)
                return [{"target_topic": record["related"], "description": record["description"]} for record in result]
        except Exception as e:
            print(f"Neo4j Query Error (get_related_topics): {e}")
            return []
            
    def add_topic(self, name: str, description: str, grade: str, subject: str):
        if not self.driver:
            return
        query = """
        MERGE (t:Topic {name: $name})
        SET t.description = $description, t.grade = $grade, t.subject = $subject
        """
        try:
            with self.driver.session() as session:
                session.run(query, name=name, description=description, grade=grade, subject=subject)
        except Exception as e:
            print(f"Neo4j Query Error (add_topic): {e}")

    def add_relationship(self, source: str, target: str, rel_type: str = "PREREQUISITE_OF"):
        if not self.driver:
            return
        query = f"""
        MATCH (s:Topic {{name: $source}})
        MATCH (t:Topic {{name: $target}})
        MERGE (s)-[:{rel_type}]->(t)
        """
        try:
            with self.driver.session() as session:
                session.run(query, source=source, target=target)
        except Exception as e:
            print(f"Neo4j Query Error (add_relationship): {e}")

neo4j_service = Neo4jKnowledgeGraphService()
