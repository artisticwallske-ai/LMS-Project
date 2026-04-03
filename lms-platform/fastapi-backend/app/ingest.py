import os
import argparse
import re
from typing import Optional, Dict, Any, List
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
import weaviate
import weaviate.classes as wvc
from app.core.config import settings
from app.core.database import supabase_client
from app.services.knowledge_graph_neo4j import neo4j_service

def get_or_create_subject(name: str, grade: str) -> str:
    response = supabase_client.table("subjects").select("id").eq("name", name).eq("grade_level", grade).execute()
    if response.data:
        return response.data[0]["id"]
    
    print(f"Creating subject: {name} ({grade})")
    response = supabase_client.table("subjects").insert({"name": name, "grade_level": grade}).execute()
    return response.data[0]["id"]

def hierarchical_chunking(docs: List[Any], subject_name: str, grade_level: str) -> List[Dict[str, Any]]:
    """
    Implements the 5-Level Chunking Hierarchy from PRD Sec 2.2 using heuristics.
    Level 0: Document (Full context)
    Level 1: Theme (e.g., 1.0, 2.0)
    Level 2: Strand (e.g., Listening, Speaking, Reading, Writing)
    Level 3: Lesson Unit (Specific Learning Outcomes)
    Level 4: Assessment (Rubrics)
    """
    chunks = []
    
    full_text = "\n".join([doc.page_content for doc in docs])
    
    # 1. Level 0: Document chunk (summary)
    chunks.append({
        "chunk_level": 0,
        "content": f"Curriculum Document for {subject_name}, {grade_level}. Full text length: {len(full_text)}",
        "metadata": {"type": "document"}
    })

    # Heuristic parsing for Themes and Strands
    # This is a simplified regex approach since KICD PDF formatting varies.
    # Look for "Theme X.0: Name" or "1.0 Name"
    theme_pattern = re.compile(r'(?:Theme\s*)?(\d+\.0)\s*([A-Za-z\s]+)(?=\n|$)')
    
    lines = full_text.split('\n')
    current_theme = "General"
    current_strand = "General"
    buffer = []
    
    for line in lines:
        theme_match = theme_pattern.search(line)
        if theme_match:
            # Save previous buffer as a lesson unit
            if buffer:
                content = "\n".join(buffer).strip()
                if len(content) > 50:
                    chunks.append({
                        "chunk_level": 3,
                        "content": content,
                        "metadata": {"theme": current_theme, "strand": current_strand, "type": "lesson"}
                    })
                buffer = []
            
            theme_num, theme_name = theme_match.groups()
            current_theme = f"{theme_num} {theme_name.strip()}"
            chunks.append({
                "chunk_level": 1,
                "content": f"Theme: {current_theme}",
                "metadata": {"theme": current_theme, "type": "theme"}
            })
            # Add to Neo4j
            neo4j_service.add_topic(current_theme, f"Theme in {subject_name}", grade_level, subject_name)
            continue
            
        # Basic strand detection
        if "Listening and Speaking" in line or "Reading" in line or "Language Use" in line or "Writing" in line:
            current_strand = line.strip()
            chunks.append({
                "chunk_level": 2,
                "content": f"Strand: {current_strand} under Theme: {current_theme}",
                "metadata": {"theme": current_theme, "strand": current_strand, "type": "strand"}
            })
            neo4j_service.add_topic(current_strand, f"Strand in {current_theme}", grade_level, subject_name)
            neo4j_service.add_relationship(current_strand, current_theme, "STRAND_IN")
            continue
            
        # Assessment rubrics detection
        if "Assessment" in line or "Rubric" in line or "Exceeds Expectations" in line:
            buffer.append(line)
            # We tag this part heavily
            if len(buffer) > 5:
                content = "\n".join(buffer).strip()
                chunks.append({
                    "chunk_level": 4,
                    "content": content,
                    "metadata": {"theme": current_theme, "strand": current_strand, "type": "assessment"}
                })
                buffer = []
            continue

        buffer.append(line)
        
        # Chunk every ~200 lines if no clear break
        if len(buffer) > 50:
            content = "\n".join(buffer).strip()
            chunks.append({
                "chunk_level": 3,
                "content": content,
                "metadata": {"theme": current_theme, "strand": current_strand, "type": "lesson"}
            })
            buffer = []
            
    if buffer:
        content = "\n".join(buffer).strip()
        if len(content) > 50:
            chunks.append({
                "chunk_level": 3,
                "content": content,
                "metadata": {"theme": current_theme, "strand": current_strand, "type": "lesson"}
            })

    return chunks

def ingest_curriculum(pdf_path: str = None, subject_name: str = "English", grade_level: str = "Grade 4") -> Dict[str, Any]:
    print(f"Starting ingestion for {subject_name} ({grade_level})...")
    
    result = {
        "status": "failed",
        "subject_id": None,
        "chunks_generated": 0,
        "message": ""
    }

    db_warning = None
    try:
        subject_id = get_or_create_subject(subject_name, grade_level)
        result["subject_id"] = subject_id
    except Exception as e:
        db_warning = str(e)
        subject_id = "unknown"

    if pdf_path is None:
        pdf_path = settings.CURRICULUM_PDF_PATH
    
    if not os.path.exists(pdf_path):
        msg = f"Error: PDF not found at {pdf_path}"
        print(msg)
        result["message"] = msg
        return result

    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
    except Exception as e:
        msg = f"Error loading PDF: {e}"
        print(msg)
        result["message"] = msg
        return result
    
    # 5-Level Hierarchical Chunking
    chunks = hierarchical_chunking(docs, subject_name, grade_level)
    print(f"Generated {len(chunks)} hierarchical chunks.")
    result["chunks_generated"] = len(chunks)
    
    print("Loading embedding model (intfloat/multilingual-e5-large)...")
    try:
        embeddings_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        
        # Connect to Weaviate
        print(f"Connecting to Weaviate at {settings.WEAVIATE_URL}...")
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(settings.WEAVIATE_URL)
            w_host = parsed_url.hostname or "localhost"
            w_port = parsed_url.port or 8080
            client = weaviate.connect_to_local(host=w_host, port=w_port)
            
            collection_name = "CurriculumChunk"
            if not client.collections.exists(collection_name):
                client.collections.create(
                    name=collection_name,
                    properties=[
                        wvc.config.Property(name="content", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="chunk_level", data_type=wvc.config.DataType.INT),
                        wvc.config.Property(name="theme", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="strand", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="type", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="subject", data_type=wvc.config.DataType.TEXT),
                        wvc.config.Property(name="grade", data_type=wvc.config.DataType.TEXT)
                    ],
                )
            
            collection = client.collections.get(collection_name)
            
            # Batch insert
            with collection.batch.dynamic() as batch:
                for chunk in chunks:
                    # Generate embedding
                    vec = embeddings_model.embed_query(chunk["content"])
                    
                    props = {
                        "content": chunk["content"],
                        "chunk_level": chunk["chunk_level"],
                        "subject": subject_name,
                        "grade": grade_level,
                    }
                    props.update(chunk["metadata"])
                    
                    batch.add_object(
                        properties=props,
                        vector=vec
                    )
                    
            print(f"Successfully inserted chunks into Weaviate.")
            client.close()
            
        except Exception as e:
            print(f"Failed to connect to Weaviate: {e}. Ensure Weaviate is running.")
            # Fallback to local FAISS if Weaviate is unavailable (for dev flexibility)
            from langchain_community.vectorstores import FAISS
            from langchain_core.documents import Document
            print("Falling back to FAISS...")
            lc_docs = [Document(page_content=c["content"], metadata={"chunk_level": c["chunk_level"], **c["metadata"]}) for c in chunks]
            vectorstore = FAISS.from_documents(lc_docs, embeddings_model)
            vectorstore.save_local(settings.FAISS_INDEX_PATH)
        
        if db_warning:
            result["status"] = "warning"
            result["message"] = f"Ingestion complete, DB warning: {db_warning}"
        else:
            result["status"] = "success"
            result["message"] = "Ingestion complete"
            
    except Exception as e:
        msg = f"Error during indexing: {e}"
        print(msg)
        result["message"] = msg
        return result

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest curriculum PDF")
    parser.add_argument("--pdf", type=str, help="Path to PDF file")
    parser.add_argument("--subject", type=str, default="English", help="Subject Name")
    parser.add_argument("--grade", type=str, default="Grade 4", help="Grade Level")
    
    args = parser.parse_args()
    res = ingest_curriculum(args.pdf, args.subject, args.grade)
    print(res)
