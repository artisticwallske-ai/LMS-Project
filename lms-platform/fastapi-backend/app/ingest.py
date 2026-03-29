import os
import argparse
from typing import Optional, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.core.config import settings
from app.core.database import supabase_client

def get_or_create_subject(name: str, grade: str) -> str:
    # Check if exists
    response = supabase_client.table("subjects").select("id").eq("name", name).eq("grade_level", grade).execute()
    if response.data:
        return response.data[0]["id"]
    
    # Create
    print(f"Creating subject: {name} ({grade})")
    response = supabase_client.table("subjects").insert({"name": name, "grade_level": grade}).execute()
    return response.data[0]["id"]

def ingest_curriculum(pdf_path: str = None, subject_name: str = "English", grade_level: str = "Grade 4") -> Dict[str, Any]:
    print(f"Starting ingestion for {subject_name} ({grade_level})...")
    
    result = {
        "status": "failed",
        "subject_id": None,
        "chunks_generated": 0,
        "message": ""
    }

    # 1. Register Subject in DB
    db_warning = None
    try:
        subject_id = get_or_create_subject(subject_name, grade_level)
        print(f"Subject ID: {subject_id}")
        result["subject_id"] = subject_id
    except Exception as e:
        db_warning = str(e)
        print(f"Warning: Database update failed: {e}")
        # Proceeding even if DB update fails, assuming vector store is primary goal for now, 
        # but in prod we might want to halt.
        subject_id = "unknown"

    # 2. Load PDF
    if pdf_path is None:
        pdf_path = settings.CURRICULUM_PDF_PATH
    
    if not os.path.exists(pdf_path):
        msg = f"Error: PDF not found at {pdf_path}"
        print(msg)
        result["message"] = msg
        return result

    print(f"Loading PDF from {pdf_path}...")
    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
    except Exception as e:
        msg = f"Error loading PDF: {e}"
        print(msg)
        result["message"] = msg
        return result
    
    # Add metadata to docs
    for doc in docs:
        doc.metadata["subject_id"] = subject_id
        doc.metadata["subject_name"] = subject_name
        doc.metadata["grade_level"] = grade_level
        doc.metadata["source"] = os.path.basename(pdf_path)
    
    # 3. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)
    print(f"Generated {len(chunks)} chunks.")
    result["chunks_generated"] = len(chunks)
    
    # 4. Embeddings
    print("Loading embedding model (intfloat/multilingual-e5-large)...")
    try:
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        
        # 5. Vector Store
        # Check if index exists to append, or create new
        save_path = settings.FAISS_INDEX_PATH
        index_file = os.path.join(save_path, "index.faiss")
        
        if os.path.exists(index_file):
            print(f"Loading existing FAISS index from {save_path}...")
            try:
                vectorstore = FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
                vectorstore.add_documents(chunks)
                print("Appended documents to existing index.")
            except Exception as e:
                print(f"Error loading index, creating new one: {e}")
                vectorstore = FAISS.from_documents(chunks, embeddings)
        else:
            print("Creating new FAISS index...")
            vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # 6. Save
        vectorstore.save_local(save_path)
        print(f"Index saved to {save_path}")
        
        if db_warning:
            result["status"] = "warning"
            result["message"] = f"Ingestion complete, but subject not saved to DB: {db_warning}"
        else:
            result["status"] = "success"
            result["message"] = "Ingestion complete"
        
    except Exception as e:
        msg = f"Error during embedding/indexing: {e}"
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
