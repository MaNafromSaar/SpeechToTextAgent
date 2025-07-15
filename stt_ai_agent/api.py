"""Web API for STT AI Agent - File-based processing for remote clients."""

print("Starting API imports...")

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import tempfile
import shutil
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import json
import sys

print("Basic imports successful...")

# Handle both direct execution and module import
try:
    from .config import load_config
    from .transcription.whisper_stt import WhisperSTT
    from .processing.ollama_processor import OllamaProcessor
    from .knowledge.knowledge_base import KnowledgeBase
    print("Relative imports successful...")
except ImportError:
    # Direct execution - add parent directory to path
    print("Using direct imports...")
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from stt_ai_agent.config import load_config
    from stt_ai_agent.transcription.whisper_stt import WhisperSTT
    from stt_ai_agent.processing.ollama_processor import OllamaProcessor
    from stt_ai_agent.knowledge.knowledge_base import KnowledgeBase
    print("Direct imports successful...")

print("All imports completed...")

app = FastAPI(title="STT AI Agent API", version="1.0.0")

# Enable CORS for all origins (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the web UI
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# Global components
config = load_config()
stt = WhisperSTT(config)
processor = OllamaProcessor(config)

# Initialize knowledge base (optional)
kb = None
try:
    kb = KnowledgeBase(config)
    print("Knowledge base initialized successfully!")
except Exception as e:
    print(f"Warning: Knowledge base initialization failed: {e}")
    print("Continuing without knowledge base...")

# Processing status tracking
processing_status: Dict[str, Dict[str, Any]] = {}


def convert_audio_to_wav(input_path: str, output_path: str) -> bool:
    """Convert audio file to WAV format using ffmpeg."""
    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',          # 16kHz sample rate (good for speech)
            '-ac', '1',              # Mono channel
            '-y',                    # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        return result.returncode == 0
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return False


@app.get("/")
async def root():
    """Serve the web interface."""
    web_dir = Path(__file__).parent.parent / "web"
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {
            "status": "healthy",
            "service": "STT AI Agent",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "web_ui": "Access the web interface at /static/index.html"
        }


@app.get("/health")
async def health_check():
    """API health check."""
    return {
        "status": "healthy",
        "service": "STT AI Agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration for the frontend."""
    return {
        "whisper_model": config["whisper"]["model"],
        "available_formats": ["improve", "email", "letter", "table", "list"],
        "max_file_size_mb": 100,
        "supported_formats": [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"],
        "sample_rates": [16000, 22050, 44100, 48000],
        "professional_features": {
            "ssl2_support": True,
            "high_quality_processing": True,
            "real_time_processing": False  # For file-based processing
        }
    }


@app.post("/api/transcribe")
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    language: str = "auto",
    model: str = "base",
    process_text: bool = True,
    format_type: str = "improve",
    save_to_kb: bool = True
):
    """
    Transcribe uploaded audio file.
    
    - **audio_file**: Audio file (WAV, MP3, M4A, OGG, FLAC, WebM)
    - **language**: Language code (auto, en, de, fr, etc.)
    - **model**: Whisper model (tiny, base, small, medium, large)
    - **process_text**: Whether to process with LLM
    - **format_type**: Processing format (improve, email, letter, table, list)
    - **save_to_kb**: Save to knowledge base
    """
    
    # Validate file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Debug: Log received parameters
    print(f"DEBUG: Received parameters - language: '{language}', model: '{model}', process_text: {process_text}, format_type: '{format_type}'")
    
    file_ext = Path(audio_file.filename).suffix.lower()
    if file_ext not in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm']:
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    # Generate processing ID
    processing_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(audio_file.filename) % 10000}"
    
    # Update status
    processing_status[processing_id] = {
        "status": "uploading",
        "filename": audio_file.filename,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            shutil.copyfileobj(audio_file.file, tmp_file)
            temp_path = tmp_file.name
        
        # Convert WebM to WAV if needed
        audio_path = temp_path
        if file_ext == '.webm':
            processing_status[processing_id]["status"] = "converting"
            wav_path = temp_path.replace(file_ext, '.wav')
            
            if convert_audio_to_wav(temp_path, wav_path):
                audio_path = wav_path
                # Clean up original file
                try:
                    Path(temp_path).unlink()
                except:
                    pass
            else:
                # Clean up and raise error
                try:
                    Path(temp_path).unlink()
                except:
                    pass
                raise HTTPException(status_code=500, detail="Failed to convert WebM audio")
        
        processing_status[processing_id]["status"] = "transcribing"
        
        # Handle language parameter - Whisper uses None for auto-detection
        whisper_language = None if language == "auto" else language
        
        # Transcribe audio
        transcription = stt.transcribe(audio_path, language=whisper_language)
        
        processing_status[processing_id].update({
            "status": "processing" if process_text else "completed",
            "transcription": transcription
        })
        
        result = {
            "processing_id": processing_id,
            "transcription": transcription,
            "processed_text": None,
            "metadata": {
                "filename": audio_file.filename,
                "language": language,
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Process with LLM if requested
        if process_text and transcription.strip():
            processed_text = processor.process_text(transcription, format_type)
            result["processed_text"] = processed_text
            processing_status[processing_id]["processed_text"] = processed_text
        
        # Save to knowledge base if requested
        if save_to_kb and transcription.strip():
            background_tasks.add_task(
                save_to_knowledge_base,
                transcription,
                result.get("processed_text", ""),
                format_type,
                audio_file.filename
            )
        
        processing_status[processing_id]["status"] = "completed"
        
        # Clean up temp files
        Path(temp_path).unlink(missing_ok=True)
        if audio_path != temp_path:
            Path(audio_path).unlink(missing_ok=True)
        
        return result
        
    except Exception as e:
        processing_status[processing_id] = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """Get processing status for a specific request."""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    return processing_status[processing_id]


@app.get("/api/status")
async def get_service_status():
    """Get overall service status."""
    ollama_available = False
    try:
        # Test if Ollama is available by trying to connect
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        ollama_available = response.status_code == 200
    except:
        ollama_available = False
    
    return {
        "whisper": "available",
        "ollama": "available" if ollama_available else "unavailable",
        "text_processing_available": ollama_available,
        "config_loaded": True,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/process-text")
async def process_text_only(
    text: str,
    format_type: str = "improve",
    save_to_kb: bool = False
):
    """Process text without audio transcription."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        processed_text = processor.process_text(text, format_type)
        
        result = {
            "original_text": text,
            "processed_text": processed_text,
            "format_type": format_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if save_to_kb:
            # TODO: Re-enable when knowledge base is implemented
            pass
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")


@app.get("/api/knowledge")
async def list_knowledge_entries(limit: int = 20, offset: int = 0):
    """List knowledge base entries."""
    # Knowledge base is currently disabled
    return {
        "entries": [],
        "limit": limit,
        "offset": offset,
        "message": "Knowledge base feature is currently disabled",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/knowledge/search")
async def search_knowledge(query: str, limit: int = 10):
    """Search knowledge base."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="No search query provided")
    
    # Knowledge base is currently disabled
    return {
        "query": query,
        "results": [],
        "count": 0,
        "message": "Knowledge base feature is currently disabled",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/models")
async def get_available_models():
    """Get available models for text processing."""
    try:
        # Get available models from processor
        available_models = []
        if processor.is_available():
            available_models = processor.get_available_models()
        
        return {
            "text_models": available_models,
            "whisper_models": ["tiny", "base", "small", "medium", "large"],
            "default_text_model": config.get("ollama", {}).get("model", "deepseek-r1:1.5b"),
            "default_whisper_model": config.get("whisper", {}).get("model", "base"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "text_models": [],
            "whisper_models": ["tiny", "base", "small", "medium", "large"],
            "default_text_model": "deepseek-r1:1.5b",
            "default_whisper_model": "base",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def save_to_knowledge_base(transcription: str, processed_text: str, format_type: str, filename: str):
    """Background task to save to knowledge base."""
    try:
        if kb:
            entry_id = kb.save_entry(original_text=transcription, processed_text=processed_text, format_type=format_type, metadata={"filename": filename})
            print(f"Saved to knowledge base: {filename} (ID: {entry_id})")
        else:
            print(f"Knowledge base disabled - would save: {filename} ({format_type})")
    except Exception as e:
        print(f"Error saving to knowledge base: {e}")


@app.put("/api/entries/{entry_id}/edit")
async def update_edited_text(entry_id: int, edited_text: str):
    """Update the edited text for a knowledge base entry and learn from corrections."""
    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    try:
        success = kb.update_edited_text(entry_id, edited_text)
        if success:
            return {"success": True, "message": "Text updated and corrections learned"}
        else:
            raise HTTPException(status_code=404, detail="Entry not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update text: {str(e)}")


@app.get("/api/entries/{entry_id}/suggestions")
async def get_text_suggestions(entry_id: int):
    """Get correction suggestions for a text based on learned patterns."""
    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    try:
        # Get the entry
        entries = kb.list_entries(limit=1000)  # Get all entries temporarily
        entry = next((e for e in entries if e["id"] == entry_id), None)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Get suggestions for the processed text
        text = entry.get("edited_text") or entry["processed_text"]
        suggestions = kb.get_corrections_for_text(text)
        
        return {
            "entry_id": entry_id,
            "text": text,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@app.get("/api/knowledge/terminology")
async def get_terminology(category: Optional[str] = None):
    """Get stored terminology, optionally filtered by category."""
    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    try:
        terminology = kb.get_terminology(category)
        return {
            "terminology": terminology,
            "category": category,
            "count": len(terminology)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get terminology: {str(e)}")


@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics and learning progress."""
    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    try:
        stats = kb.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/api/entries")
async def list_entries(limit: int = 50):
    """List recent knowledge base entries."""
    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    try:
        entries = kb.list_entries(limit)
        return {
            "entries": entries,
            "count": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list entries: {str(e)}")


def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    try:
        print("Starting API server...")
        start_api_server()
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
