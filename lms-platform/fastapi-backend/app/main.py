from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import os
import shutil
import time
from typing import List, Optional
from datetime import date
from uuid import UUID
import sentry_sdk

# RAG Imports
from langchain_community.vectorstores import FAISS
from langchain_weaviate.vectorstores import WeaviateVectorStore
import weaviate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import settings
from app.ingest import ingest_curriculum

def cleanup_audio_files():
    """
    Deletes audio files in the static/audio directory that are older than 24 hours.
    """
    audio_dir = os.path.join(settings.BASE_DIR, "static", "audio")
    if not os.path.exists(audio_dir):
        return

    print(f"Cleaning up old audio files in {audio_dir}...")
    now = time.time()
    count = 0
    try:
        for filename in os.listdir(audio_dir):
            filepath = os.path.join(audio_dir, filename)
            # Check if it's a file
            if os.path.isfile(filepath):
                # Check modification time
                if os.stat(filepath).st_mtime < now - 86400: # 24 hours
                    os.remove(filepath)
                    count += 1
        if count > 0:
            print(f"Cleanup: Deleted {count} old audio files.")
    except Exception as e:
        print(f"Error during audio cleanup: {e}")

# Voice Services
from app.services.stt import get_stt_service
from app.services.tts import get_tts_service

# New Services
from app.services.timetable import timetable_service
from app.services.assessment import assessment_service
from app.services.tracks import track_service
from app.services.notification import notification_service
from app.agents.factory import agent_factory
from app.schemas import TimetableCreate, TimetableOut, SBARecordCreate, SBARecordOut, MockExamRequest, MockExamResponse, Track, NotificationOut
from app.core.cache import init_redis, get_cached_data, set_cached_data

# Global variables for RAG
vectorstore = None
embeddings = None
llm = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Sentry
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
        print("Sentry initialized.")

    # Load models on startup
    global vectorstore, embeddings
    print(f"Startup: Current working directory: {os.getcwd()}")
    print(f"Data Directory: {settings.DATA_DIR}")

    # Initialize Redis Cache
    await init_redis()
    
    # Clean up old audio files
    cleanup_audio_files()

    # Initialize Voice Services (Lazy load or pre-load)
    # Commented out to allow faster startup. Services will load on first request.
    # print("Initializing Voice Services...")
    # try:
    #     get_stt_service() # Pre-load Whisper
    #     get_tts_service() # Pre-load Chatterbox
    #     print("Voice services initialized.")
    # except Exception as e:
    #     print(f"Warning: Voice services failed to initialize: {e}")

    print("Loading embedding model...")
    try:
        # Using the same model as ingest.py
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        
        # Check for index using absolute path from settings
        index_path = settings.FAISS_INDEX_PATH
        index_file = os.path.join(index_path, "index.faiss")
        print(f"Looking for FAISS index at: {index_path}")
        
        # Check if the index directory or the specific index file is missing
        if not os.path.exists(index_path) or not os.path.exists(index_file):
            print(f"Index not found at {index_path}. Generating now...")
            try:
                ingest_curriculum()
                print("Index generated successfully.")
            except Exception as ingest_error:
                print(f"Critical Error: Failed to generate index: {ingest_error}")
        
        print(f"Connecting to Weaviate at {settings.WEAVIATE_URL}...")
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(settings.WEAVIATE_URL)
            w_host = parsed_url.hostname or "localhost"
            w_port = parsed_url.port or 8080
            weaviate_client = weaviate.connect_to_local(host=w_host, port=w_port)
            vectorstore = WeaviateVectorStore(weaviate_client, "CurriculumChunk", text_key="content", embedding=embeddings)
            print("Connected to Weaviate. RAG system ready.")
        except Exception as we_err:
            print(f"Failed to connect to Weaviate: {we_err}. Falling back to FAISS.")
            if os.path.exists(index_path) and os.path.exists(index_file):
                print(f"Loading FAISS index from {index_path}...")
                vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
                print("RAG system (FAISS fallback) ready.")
            else:
                print("Error: RAG system could not be initialized. FAISS Index missing and Weaviate unavailable.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error loading RAG models: {e}")

    # Initialize LLM
    try:
        if settings.LLM_API_KEY:
            print(f"Initializing LLM: {settings.LLM_PROVIDER} / {settings.LLM_MODEL}")
            global llm
            
            if settings.LLM_PROVIDER == "anthropic":
                # Placeholder for Anthropic support if library was added
                # from langchain_anthropic import ChatAnthropic
                # llm = ChatAnthropic(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
                print("Anthropic provider selected but langchain-anthropic not installed. Falling back to OpenAI compatible.")
            
            # Default to OpenAI compatible (works for OpenAI, Groq, OpenRouter)
            base_url = settings.LLM_BASE_URL
            
            # Auto-configure Base URL for known providers if not set
            if not base_url:
                if settings.LLM_PROVIDER == "groq":
                    base_url = "https://api.groq.com/openai/v1"
                elif settings.LLM_PROVIDER == "openrouter":
                    base_url = "https://openrouter.ai/api/v1"
            
            llm = ChatOpenAI(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                base_url=base_url,
                temperature=0.7
            )
            print("LLM initialized successfully.")
            
            # Pass LLM to agents
            from app.agents.alignment import alignment_agent
            from app.agents.tutor import tutor_agent
            from app.agents.parent_support import parent_support_agent
            alignment_agent.llm = llm
            tutor_agent.llm = llm
            parent_support_agent.llm = llm
        else:
            print("Warning: LLM_API_KEY not found. Lesson generation will use mock responses.")
            
    except Exception as e:
        print(f"Error initializing LLM: {e}")

    yield
    
    # Clean up if needed
    from app.services.knowledge_graph_neo4j import neo4j_service
    if neo4j_service:
        neo4j_service.close()

app = FastAPI(title="LMS Platform Backend", version="0.1.0", lifespan=lifespan)

# Mount static files for audio
static_dir = os.path.join(settings.BASE_DIR, "static")
audio_dir = os.path.join(static_dir, "audio")
os.makedirs(audio_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

# --- Lesson Generation Endpoints ---

class LessonRequest(BaseModel):
    topic: str
    grade: Optional[str] = "Grade 4"
    subject: Optional[str] = "English"
    is_practical: Optional[bool] = False

class LessonResponse(BaseModel):
    title: str
    content: str
    sources: List[str]

@app.post("/api/v1/lesson", response_model=LessonResponse)
async def generate_lesson(request: LessonRequest):
    """
    Generate a lesson plan based on the requested topic using Subject Agents.
    """
    # 0. Check Cache
    cache_key = f"lesson:{request.grade}:{request.subject}:{request.topic}:{request.is_practical}".lower().replace(" ", "_")
    cached_lesson = await get_cached_data(cache_key)
    if cached_lesson:
        print(f"Cache hit for {cache_key}")
        return LessonResponse(**cached_lesson)

    # 1. Select Agent
    agent = agent_factory.get_agent(request.subject)
    print(f"Selected Agent: {agent.__class__.__name__} for subject: {request.subject}")

    # 2. Delegate Generation to Agent
    # Note: vectorstore and llm are global variables in main.py
    try:
        result = await agent.generate_lesson(
            topic=request.topic,
            grade=request.grade,
            vectorstore=vectorstore,
            llm=llm,
            is_practical=request.is_practical
        )
        
        response_data = LessonResponse(
            title=result["title"],
            content=result["content"],
            sources=result["sources"]
        )

        # Cache the result (TTL 24 hours)
        await set_cached_data(cache_key, response_data.model_dump(), ttl=86400)
        
        return response_data
        
    except Exception as e:
        print(f"Lesson Generation Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate lesson: {str(e)}")

# --- Voice Endpoints (Placeholders) ---

class TTSRequest(BaseModel):
    text: str
    language: str = "en"  # "en" or "sw"
    voice_id: str = "default"

@app.post("/api/v1/tts")
async def text_to_speech(request: TTSRequest):
    """
    Generate audio from text using TTS.
    Returns a URL to the generated audio file.
    """
    try:
        tts = get_tts_service()
        if not tts or not tts.model:
             raise HTTPException(status_code=503, detail="TTS service unavailable")

        audio_path = await tts.generate_audio(request.text, request.language)
        
        # Construct URL relative to current host
        # Ideally, we should use request.base_url, but for simplicity:
        filename = os.path.basename(audio_path)
        audio_url = f"/static/audio/{filename}"
        
        return {"audio_url": audio_url, "text": request.text, "language": request.language}
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/stt")
async def speech_to_text(file: UploadFile = File(...), language: Optional[str] = Form(None)):
    """
    Transcribe audio file using Whisper.
    """
    try:
        stt = get_stt_service()
        if not stt or not stt.model:
             raise HTTPException(status_code=503, detail="STT service unavailable")
        
        # Save uploaded file temporarily
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            text = stt.transcribe(temp_filename, language=language)
        finally:
            # Cleanup
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        
        return {"text": text}
    except Exception as e:
        print(f"STT Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Conversational Voice Tutor Endpoint ---
from app.agents.tutor import tutor_agent

class VoiceChatResponse(BaseModel):
    transcript: str
    reply_text: str
    audio_url: str

@app.post("/api/v1/chat/voice", response_model=VoiceChatResponse)
async def voice_chat(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    language: str = Form("en"),
    context: str = Form("")
):
    try:
        # 1. STT
        stt = get_stt_service()
        if not stt or not stt.model:
             raise HTTPException(status_code=503, detail="STT service unavailable")
        
        temp_filename = f"temp_chat_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            user_text = stt.transcribe(temp_filename, language=language if language != "auto" else None)
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
        if not user_text.strip():
            return {"transcript": "", "reply_text": "I didn't catch that.", "audio_url": ""}

        # 2. LLM (Tutor Agent)
        reply_text = await tutor_agent.get_response(session_id, user_text, context)

        # 3. TTS
        tts = get_tts_service()
        audio_url = ""
        if tts and tts.model:
            audio_path = await tts.generate_audio(reply_text, language)
            filename = os.path.basename(audio_path)
            audio_url = f"/static/audio/{filename}"

        return {
            "transcript": user_text,
            "reply_text": reply_text,
            "audio_url": audio_url
        }

    except Exception as e:
        print(f"Voice Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Timetable Endpoints ---

class TimetableGenerateRequest(BaseModel):
    learner_id: UUID
    start_date: date
    term: int
    grade_level: Optional[str] = None # Optional override

@app.post("/api/v1/timetable/generate", response_model=TimetableOut)
async def generate_timetable_endpoint(request: TimetableGenerateRequest):
    """
    Generate a weekly timetable for a learner.
    """
    try:
        timetable = timetable_service.generate_timetable(
            request.learner_id, 
            request.start_date, 
            request.term,
            request.grade_level
        )
        return timetable
    except Exception as e:
        print(f"Timetable Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/timetable/{timetable_id}", response_model=TimetableOut)
async def get_timetable_endpoint(timetable_id: str):
    """
    Get a specific timetable by ID.
    """
    timetable = timetable_service.get_timetable(timetable_id)
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    return timetable

# --- SBA Assessment Endpoints ---

@app.post("/api/v1/sba/record", response_model=SBARecordOut)
async def record_sba_endpoint(record: SBARecordCreate):
    """
    Record a School-Based Assessment result.
    """
    try:
        return assessment_service.record_sba_result(record)
    except Exception as e:
        print(f"SBA Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sba/learner/{learner_id}", response_model=List[SBARecordOut])
async def get_sba_history_endpoint(learner_id: UUID):
    """
    Get SBA history for a learner.
    """
    return assessment_service.get_learner_sba_history(learner_id)

@app.get("/api/v1/analytics/longitudinal/{learner_id}")
async def get_longitudinal_analytics_endpoint(learner_id: UUID):
    """
    Get longitudinal mastery progress for a learner.
    """
    return assessment_service.get_longitudinal_analytics(learner_id)

@app.post("/api/v1/sba/{record_id}/acknowledge")
async def acknowledge_sba_endpoint(record_id: UUID):
    """
    Parent acknowledges an SBA result.
    """
    success = assessment_service.acknowledge_sba(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "success"}

@app.post("/api/v1/assessment/generate-mock", response_model=MockExamResponse)
async def generate_mock_exam_endpoint(request: MockExamRequest):
    """
    Generate a mock exam for KJSEA preparation.
    """
    try:
        # Pass global vectorstore and llm
        return await assessment_service.generate_mock_exam(request, vectorstore, llm)
    except Exception as e:
        print(f"Mock Exam Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Curriculum & Subjects Endpoints ---

@app.get("/api/v1/agents/subjects", response_model=List[str])
async def get_supported_agent_subjects():
    """
    List subjects that have specialized AI agents available for lesson generation.
    """
    return agent_factory.get_supported_subjects()

@app.get("/api/v1/subjects")
async def get_subjects(grade_level: Optional[str] = None, track: Optional[str] = None):
    """
    List all available subjects, optionally filtered by grade level and track.
    """
    try:
        from app.core.database import supabase_client
        query = supabase_client.table("subjects").select("*")
        if grade_level:
            query = query.eq("grade_level", grade_level)
            
        response = query.execute()
        subjects = response.data

        # Filter by track if provided and relevant (SSS)
        if track and track != "None" and grade_level in ["Grade 10", "Grade 11", "Grade 12"]:
            # Get allowed subjects for this track
            # We need to map the string track to the Enum
            track_enum = None
            for t in Track:
                if t.value == track:
                    track_enum = t
                    break
            
            if track_enum:
                track_data = track_service.get_subjects_for_track(track_enum)
                allowed_names = set(track_data["core"] + track_data["electives"])
                # Filter subjects where name is in allowed_names
                subjects = [s for s in subjects if s["name"] in allowed_names]

        return subjects
    except Exception as e:
        print(f"Error fetching subjects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/curriculum/upload")
def upload_curriculum(
    file: UploadFile = File(...),
    subject_name: str = Form(...),
    grade_level: str = Form("Grade 4")
):
    """
    Upload a curriculum PDF and ingest it into the RAG system.
    Note: Removed 'async' to run in threadpool since ingest is synchronous/blocking.
    """
    try:
        # Ensure data directory exists
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        
        # Sanitize filename
        safe_name = "".join(c for c in subject_name if c.isalnum() or c in (' ', '_', '-')).strip()
        filename = f"{safe_name}_{grade_level}.pdf".replace(" ", "_")
        file_path = os.path.join(settings.DATA_DIR, filename)
        
        print(f"Saving uploaded file to: {file_path}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"File saved successfully. Starting ingestion...")
        
        # Ingest
        result = ingest_curriculum(file_path, subject_name, grade_level)
        
        if result["status"] == "failed":
            print(f"Ingestion Failed: {result}")
            raise HTTPException(status_code=500, detail=result["message"])
            
        return result
        
    except Exception as e:
        print(f"CRITICAL UPLOAD ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

# --- Track Selection Endpoints ---

@app.get("/api/v1/tracks")
async def get_tracks():
    """
    List all available Senior Secondary School tracks.
    """
    return track_service.get_track_options()

@app.get("/api/v1/tracks/{track_name}/subjects")
async def get_track_subjects(track_name: str):
    """
    Get subjects for a specific track.
    """
    try:
        # Convert string to Enum, handling case sensitivity or URL encoding if needed
        # Assuming exact match for now, or use upper case
        track_enum = None
        for t in Track:
            if t.value == track_name or t.name == track_name.upper():
                track_enum = t
                break
        
        if not track_enum:
             raise HTTPException(status_code=404, detail="Track not found")
             
        return track_service.get_subjects_for_track(track_enum)
    except Exception as e:
        print(f"Error fetching track subjects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/learner/{learner_id}/track")
async def get_learner_track(learner_id: UUID):
    """
    Get the currently selected track for a learner.
    """
    track = track_service.get_learner_track(learner_id)
    return {"track": track}

@app.put("/api/v1/learner/{learner_id}/track")
async def update_learner_track(learner_id: UUID, track: Track):
    """
    Update the learner's track selection.
    """
    try:
        result = track_service.update_learner_track(learner_id, track)
        return {"status": "success", "track": track, "data": result}
    except Exception as e:
        print(f"Error updating learner track: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Notification Endpoints ---

@app.get("/api/v1/notifications/{learner_id}", response_model=List[NotificationOut])
async def get_notifications(learner_id: UUID, unread_only: bool = False):
    """
    Get notifications for a learner.
    """
    return notification_service.get_learner_notifications(learner_id, unread_only)

@app.put("/api/v1/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: UUID):
    """
    Mark a notification as read.
    """
    success = notification_service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}

@app.get("/api/v1/parent/tip")
async def get_parent_tip(topic: str = "General", grade: str = "Grade 4"):
    """
    Generate a daily teaching tip for parents.
    """
    from app.agents.parent_support import parent_support_agent
    tip = await parent_support_agent.generate_tip(topic, grade)
    return {"tip": tip}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
