"""Simplified STT API for browser-based audio processing."""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Only import what we need for local processing
from .config import load_config
from .transcription.whisper_stt import WhisperSTT
from .processing.enhanced_processor import LocalTextProcessor

app = FastAPI(
    title="STT AI Agent API",
    description="Speech-to-Text processing for professional audio interfaces",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount web UI static files
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# Global configuration and local services
config = load_config()
stt = WhisperSTT(config)

# Initialize text processor with error handling
text_processor = None
try:
    text_processor = LocalTextProcessor(config)
except Exception as e:
    print(f"Warning: Text processor not available: {e}")
    print("Text processing features will be disabled.")

# Processing status tracking
processing_status: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI."""
    index_file = web_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text())
    else:
        return HTMLResponse("""
        <h1>STT AI Agent API</h1>
        <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
        <p>Web UI not found at expected location.</p>
        """)


@app.get("/health")
async def health_check():
    """API health check."""
    return {
        "status": "healthy",
        "service": "STT AI Agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "whisper_available": True
    }


@app.get("/api/config")
async def get_config():
    """Get configuration for frontend."""
    available_providers = []
    supported_tasks = []
    supported_languages = []
    
    if text_processor:
        available_providers = text_processor.get_available_providers()
        supported_tasks = text_processor.get_supported_tasks()
        supported_languages = text_processor.get_supported_languages()
    
    return {
        "whisper_model": config.get("whisper", {}).get("model", "base"),
        "available_models": ["tiny", "base", "small", "medium", "large"],
        "supported_formats": [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"],
        "max_file_size_mb": 100,
        "sample_rates": [16000, 22050, 44100, 48000],
        "professional_features": {
            "ssl2_support": True,
            "high_quality_processing": True,
            "browser_recording": True
        },
        "text_processing": {
            "available_providers": available_providers,
            "supported_tasks": supported_tasks,
            "supported_languages": supported_languages,
            "enabled": text_processor is not None
        }
    }


@app.post("/api/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str = Form("auto"),
    model: str = Form("base"),
    process_text: bool = Form(False),
    format_type: str = Form("improve"),
    save_to_kb: bool = Form(False)
):
    """
    Transcribe uploaded audio file.
    
    - **audio_file**: Audio file (WAV, MP3, M4A, OGG, FLAC, WEBM)
    - **language**: Language code (auto, en, de, fr, etc.)
    - **model**: Whisper model (tiny, base, small, medium, large)
    """
    
    # Validate file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    print(f"DEBUG: Received file: {audio_file.filename}, Content-Type: {audio_file.content_type}")
    
    file_ext = Path(audio_file.filename).suffix.lower()
    supported_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm']
    
    if file_ext not in supported_formats:
        print(f"DEBUG: Unsupported format {file_ext}, supported: {supported_formats}")
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {file_ext}. Supported: {', '.join(supported_formats)}")
    
    # Generate processing ID
    processing_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(audio_file.filename) % 10000}"
    
    # Update status
    processing_status[processing_id] = {
        "status": "uploading",
        "filename": audio_file.filename,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        processing_status[processing_id]["status"] = "transcribing"
        
        # Transcribe audio
        transcription = stt.transcribe(temp_path, language=language if language != "auto" else None)
        
        processing_status[processing_id].update({
            "status": "completed",
            "transcription": transcription
        })
        
        result = {
            "processing_id": processing_id,
            "transcription": transcription,
            "metadata": {
                "filename": audio_file.filename,
                "language": language,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "file_size_bytes": len(content)
            },
            "success": True
        }
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return result
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        processing_status[processing_id] = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/api/transcribe-and-process")
async def transcribe_and_process(
    audio_file: UploadFile = File(...),
    language: str = Form("auto"),
    model: str = Form("base"),
    process_text: bool = Form(True),
    task_type: str = Form("improve"),
    text_model: str = Form("llama3"),
    target_language: str = Form("")
):
    """
    Full pipeline: transcribe audio and process with local LLM.
    
    - **audio_file**: Audio file (WAV, MP3, M4A, OGG, FLAC, WebM)
    - **language**: Language code for transcription (auto, en, de, fr, etc.)
    - **model**: Whisper model (tiny, base, small, medium, large)
    - **process_text**: Whether to process transcribed text
    - **task_type**: Processing task (improve, email, letter, table, list, translate)
    - **text_model**: Local LLM model to use
    - **target_language**: Target language for translation
    """
    import time
    start_time = time.time()
    
    # Validate file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_ext = Path(audio_file.filename).suffix.lower()
    if file_ext not in ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm']:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {file_ext}")
    
    processing_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(audio_file.filename) % 10000}"
    
    processing_status[processing_id] = {
        "status": "uploading",
        "filename": audio_file.filename,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        processing_status[processing_id]["status"] = "transcribing"
        
        # Transcribe audio
        transcription = stt.transcribe(temp_path, language=language if language != "auto" else None)
        transcription_time = time.time() - start_time
        
        result = {
            "processing_id": processing_id,
            "transcription": transcription,
            "processed_text": None,
            "metadata": {
                "filename": audio_file.filename,
                "language": language,
                "whisper_model": model,
                "timestamp": datetime.now().isoformat(),
                "file_size_bytes": len(content),
                "transcription_time": transcription_time
            },
            "success": True
        }
        
        # Process text if requested
        if process_text and transcription.strip():
            if not text_processor:
                raise HTTPException(status_code=503, detail="Text processing not available. Please install and start Ollama.")
            
            processing_status[processing_id]["status"] = "processing_text"
            
            processing_start = time.time()
            processed_text = text_processor.process_text(
                transcription, 
                task_type=task_type,
                model=text_model,
                target_language=target_language if target_language else None
            )
            processing_time = time.time() - processing_start
            
            result["processed_text"] = processed_text
            result["metadata"]["text_processing_time"] = processing_time
            result["metadata"]["text_model"] = text_model
            result["metadata"]["task_type"] = task_type
        
        processing_status[processing_id].update({
            "status": "completed",
            "transcription": transcription,
            "processed_text": result.get("processed_text")
        })
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return result
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        processing_status[processing_id] = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/process-text")
async def process_text_only(
    text: str = Form(...),
    task_type: str = Form("improve"),
    model: str = Form("llama3"),
    target_language: str = Form("")
):
    """
    Process text with local LLM.
    
    - **text**: Text to process
    - **task_type**: Processing task (improve, email, letter, table, list, translate)
    - **model**: Local LLM model to use
    - **target_language**: Target language for translation
    """
    if not text_processor:
        raise HTTPException(status_code=503, detail="Text processing not available. Please install and start Ollama.")
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        import time
        start_time = time.time()
        
        processed_text = text_processor.process_text(
            text,
            task_type=task_type,
            model=model,
            target_language=target_language if target_language else None
        )
        
        processing_time = time.time() - start_time
        
        return {
            "original_text": text,
            "processed_text": processed_text,
            "metadata": {
                "task_type": task_type,
                "model": model,
                "target_language": target_language,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            },
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")


@app.get("/api/models")
async def get_available_models():
    """Get available local models and capabilities."""
    try:
        if not text_processor:
            return {
                "whisper_models": ["tiny", "base", "small", "medium", "large"],
                "text_models": [],
                "recommended_models": config.get("local_models", {}).get("recommended_models", []),
                "task_types": [],
                "languages": [],
                "providers": [],
                "text_processing_available": False
            }
        
        return {
            "whisper_models": ["tiny", "base", "small", "medium", "large"],
            "text_models": text_processor.get_available_models(),
            "recommended_models": config.get("local_models", {}).get("recommended_models", []),
            "task_types": text_processor.get_supported_tasks(),
            "languages": text_processor.get_supported_languages(),
            "providers": text_processor.get_available_providers(),
            "text_processing_available": True
        }
    except Exception as e:
        return {
            "whisper_models": ["tiny", "base", "small", "medium", "large"],
            "text_models": [],
            "error": str(e),
            "text_processing_available": False
        }


@app.post("/api/pull-model")
async def pull_model(model_name: str = Form(...)):
    """Pull a model from Ollama library."""
    if not text_processor:
        raise HTTPException(status_code=503, detail="Text processing not available. Please install and start Ollama.")
    
    try:
        success = text_processor.pull_model(model_name)
        if success:
            return {"success": True, "message": f"Model {model_name} pulled successfully"}
        else:
            return {"success": False, "message": f"Failed to pull model {model_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model pull failed: {str(e)}")


@app.get("/api/providers")
async def get_providers():
    """Get available LLM providers and their status."""
    if not text_processor:
        return {"available_providers": [], "text_processing_enabled": False}
    
    return {
        "available_providers": text_processor.get_available_providers(),
        "supported_tasks": text_processor.get_supported_tasks(),
        "supported_languages": text_processor.get_supported_languages(),
        "text_processing_enabled": True
    }


@app.get("/api/status")
async def get_service_status():
    """Get overall service status."""
    providers = []
    if text_processor:
        providers = text_processor.get_available_providers()
    
    return {
        "whisper": "available",
        "text_processing": "available" if text_processor else "disabled",
        "available_providers": providers,
        "config_loaded": True,
        "active_processes": len(processing_status),
        "timestamp": datetime.now().isoformat()
    }


def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    print(f"Starting STT AI Agent API on {host}:{port}")
    print(f"Web UI available at: http://{host}:{port}")
    print(f"API docs available at: http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api_server()
