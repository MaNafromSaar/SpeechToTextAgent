"""Core STT Service - Lightweight transcription and processing service."""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Literal
import subprocess
import whisper
import torch

app = FastAPI(title="STT Core Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration
KNOWLEDGE_BASE_URL = "http://knowledge-service:8001"
OLLAMA_URL = "http://ollama:11434"

# ASR Models
whisper_model = None

@app.on_event("startup")
async def startup_event():
    global whisper_model
    print("Loading Whisper model...")
    # Use GPU if available, otherwise CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Use larger model for better German recognition
    model_name = "large-v3"  # Better for German language
    try:
        whisper_model = whisper.load_model(model_name, device=device)
        print(f"Whisper model '{model_name}' loaded on {device}")
    except Exception as e:
        print(f"Failed to load {model_name}, falling back to base: {e}")
        whisper_model = whisper.load_model("base", device=device)
        print(f"Whisper model 'base' loaded on {device}")

# Data models
class ProcessRequest(BaseModel):
    text: str
    format_type: str = "ollama_correction"

class ProcessResponse(BaseModel):
    original_text: str
    processed_text: str
    suggestions: Optional[list] = None

class TranscribeRequest(BaseModel):
    asr_model: Literal["whisper"] = "whisper"

class KnowledgeClient:
    """Client for communicating with Knowledge Base service."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def save_entry(self, original_text: str, processed_text: str, format_type: str, metadata: Optional[Dict] = None):
        """Save entry to knowledge base."""
        try:
            response = requests.post(f"{self.base_url}/entries", json={
                "original_text": original_text,
                "processed_text": processed_text,
                "format_type": format_type,
                "metadata": metadata or {}
            }, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to save to knowledge base: {e}")
            return None
    
    def search(self, query: str, limit: int = 5):
        """Search knowledge base."""
        try:
            response = requests.post(f"{self.base_url}/search", json={
                "query": query,
                "limit": limit
            }, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to search knowledge base: {e}")
            return None
    
    def get_corrections(self, text: str):
        """Get correction suggestions."""
        try:
            response = requests.get(f"{self.base_url}/corrections/{text}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get corrections: {e}")
            return None

# Global clients
kb_client = KnowledgeClient(KNOWLEDGE_BASE_URL)

def convert_audio_to_wav(input_path: str, output_path: str) -> bool:
    """Convert audio file to WAV format using ffmpeg."""
    try:
        command = [
            "ffmpeg", "-i", input_path, 
            "-acodec", "pcm_s16le", 
            "-ar", "16000", 
            "-ac", "1", 
            output_path, "-y"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Audio conversion failed: {e}")
        return False
    except FileNotFoundError:
        print("ffmpeg not found")
        return False

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Whisper."""
    global whisper_model
    
    if whisper_model is None:
        raise HTTPException(status_code=500, detail="Whisper model not loaded")
    
    try:
        result = whisper_model.transcribe(audio_path, language="de")
        return result["text"].strip()
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Whisper transcription failed: {str(e)}")

def transcribe_audio_with_model(audio_path: str, asr_model: str) -> str:
    """Transcribe audio using specified ASR model (Whisper only)."""
    if asr_model != "whisper":
        raise HTTPException(status_code=400, detail="Only Whisper model is supported")
    
    return transcribe_audio(audio_path)

def process_text_with_ollama(text: str) -> str:
    """Process text using Ollama with German-optimized model."""
    # List of models to try in order of preference for German (updated based on testing)
    german_models = ["phi3.5:3.8b", "mistral:7b", "thinkverse/towerinstruct:latest", "llama3.2:3b"]
    
    prompt = f"""Korrigiere bitte den folgenden deutschen Text. Behalte den ursprünglichen Inhalt und Stil bei. Verbessere nur Grammatik, Rechtschreibung und natürlichen Wortfluss. Antworte nur mit dem korrigierten Text:

{text}"""

    for model in german_models:
        try:
            response = requests.post(f"{OLLAMA_URL}/api/generate", json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "keep_alive": "5m"
                }
            }, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                corrected_text = result.get("response", text).strip()
                print(f"Text processed successfully with model: {model}")
                return corrected_text
                
        except Exception as e:
            print(f"Failed to process with {model}: {e}")
            continue
    
    print("All German models failed, returning original text")
    return text

@app.get("/health")
async def health():
    """Return service health and model availability status."""
    
    # Check Whisper availability
    whisper_status = "available" if whisper_model else "unavailable"
    
    # Check Ollama availability and German models
    ollama_status = "unavailable"
    text_processing_available = False
    available_german_models = []
    
    try:
        ollama_response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if ollama_response.status_code == 200:
            models_data = ollama_response.json().get("models", [])
            if models_data:
                ollama_status = "available"
                text_processing_available = True
                
                # Check which German models are available
                german_models = ["mistral:7b", "phi3.5:3.8b", "thinkverse/towerinstruct:latest", "llama3.2:3b"]
                model_names = [model["name"] for model in models_data]
                available_german_models = [model for model in german_models if model in model_names]
                
    except Exception as e:
        print(f"Health check failed: {e}")
    
    return {
        "status": "ok", 
        "service": "STT Core Service",
        "whisper": whisper_status,
        "ollama": ollama_status,
        "text_processing_available": text_processing_available,
        "available_german_models": available_german_models,
        "whisper_device": "cuda" if torch.cuda.is_available() else "cpu"
    }

@app.post("/transcribe", response_model=ProcessResponse)
async def transcribe_and_process(
    file: UploadFile = File(...),
    language: str = Form("de"),
    model: str = Form("base"),
    process_text: str = Form("true"),
    asr_model: str = Form("whisper")
):
    """Transcribe audio file and process the text with selectable ASR model."""
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_input:
        shutil.copyfileobj(file.file, temp_input)
        temp_input_path = temp_input.name
    
    try:
        # Convert to WAV if needed
        if not file.filename.lower().endswith('.wav'):
            temp_wav_path = temp_input_path + ".wav"
            if not convert_audio_to_wav(temp_input_path, temp_wav_path):
                raise HTTPException(status_code=400, detail="Audio conversion failed")
            audio_path = temp_wav_path
        else:
            audio_path = temp_input_path
        
        # Transcribe audio with selected ASR model
        transcript = transcribe_audio_with_model(audio_path, asr_model)
        
        # Process with Ollama
        processed_text = process_text_with_ollama(transcript)
        
        # Get suggestions from knowledge base
        suggestions = None
        corrections_result = kb_client.get_corrections(transcript)
        if corrections_result:
            suggestions = corrections_result.get("suggestions", [])
        
        # Save to knowledge base
        kb_client.save_entry(
            original_text=transcript,
            processed_text=processed_text,
            format_type="ollama_correction",
            metadata={"filename": file.filename}
        )
        
        return ProcessResponse(
            original_text=transcript,
            processed_text=processed_text,
            suggestions=suggestions
        )
        
    finally:
        # Cleanup temp files
        Path(temp_input_path).unlink(missing_ok=True)
        if 'temp_wav_path' in locals():
            Path(temp_wav_path).unlink(missing_ok=True)

@app.post("/process-text", response_model=ProcessResponse)
async def process_text_only(request: ProcessRequest):
    """Process text without transcription."""
    
    # Process with Ollama
    processed_text = process_text_with_ollama(request.text)
    
    # Get suggestions from knowledge base
    suggestions = None
    corrections_result = kb_client.get_corrections(request.text)
    if corrections_result:
        suggestions = corrections_result.get("suggestions", [])
    
    # Save to knowledge base
    kb_client.save_entry(
        original_text=request.text,
        processed_text=processed_text,
        format_type=request.format_type,
        metadata={}
    )
    
    return ProcessResponse(
        original_text=request.text,
        processed_text=processed_text,
        suggestions=suggestions
    )

def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds."""
    try:
        import librosa
        duration = librosa.get_duration(filename=audio_path)
        return round(duration, 2)
    except:
        return 0.0

# Add new endpoints for testing
@app.post("/transcribe-only")
async def transcribe_only(
    file: UploadFile = File(...),
    asr_model: str = Form("whisper")
):
    """Transcribe audio file only, without text processing."""
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_input:
        shutil.copyfileobj(file.file, temp_input)
        temp_input_path = temp_input.name
    
    try:
        # Convert to WAV if needed
        if not file.filename.lower().endswith('.wav'):
            temp_wav_path = temp_input_path + ".wav"
            if not convert_audio_to_wav(temp_input_path, temp_wav_path):
                raise HTTPException(status_code=400, detail="Audio conversion failed")
            audio_path = temp_wav_path
        else:
            audio_path = temp_input_path
        
        # Transcribe audio with selected ASR model
        transcript = transcribe_audio_with_model(audio_path, asr_model)
        
        return {
            "transcription": transcript,
            "asr_model": asr_model,
            "audio_duration": get_audio_duration(audio_path)
        }
        
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        try:
            Path(temp_input_path).unlink()
            if 'temp_wav_path' in locals():
                Path(temp_wav_path).unlink()
        except:
            pass

@app.post("/correct-text")
async def correct_text_only(request: ProcessRequest):
    """Correct text only, without transcription."""
    try:
        processed_text = process_text_with_ollama(request.text)
        
        return {
            "original_text": request.text,
            "corrected_text": processed_text,
            "correction_model": "phi3.5:3.8b (primary German model)"
        }
        
    except Exception as e:
        print(f"Text correction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/asr")
async def get_asr_models():
    """Get available ASR models and their status."""
    return {
        "whisper": {
            "name": "OpenAI Whisper",
            "status": "loaded" if whisper_model else "not_loaded",
            "language": "multilingual",
            "size": "~39MB",
            "optimized": True
        }
    }

@app.get("/models/correction")
async def get_correction_models():
    """Get available text correction models."""
    return {
        "llama3.1:8b": {
            "name": "Llama 3.1 8B",
            "status": "active",
            "language": "german",
            "quality": "excellent",
            "size": "4.9GB"
        },
        "llama3.2:3b": {
            "name": "Llama 3.2 3B", 
            "status": "available",
            "language": "german",
            "quality": "good",
            "size": "2.0GB"
        }
    }
