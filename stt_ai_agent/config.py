"""Configuration management for STT AI Agent."""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables and .env file."""
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
    
    config = {
        # Whisper Configuration - Upgraded for better German recognition
        "whisper": {
            "model": os.getenv("WHISPER_MODEL", "large-v3"),  # Better for German
            "device": os.getenv("WHISPER_DEVICE", "cuda"),
            "language": os.getenv("WHISPER_LANGUAGE", "de"),
        },
        
        # Ollama Configuration - Upgraded for better German processing
        "ollama": {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "mistral:7b"),  # Superior German capabilities
            "fallback_model": os.getenv("OLLAMA_FALLBACK_MODEL", "phi3.5:3.8b"),  # Alternative German model
        },
        
        # Enhanced Local Text Processing Configuration
        "text_processing": {
            "default_provider": "ollama",  # Local only
            "default_model": os.getenv("TEXT_PROCESSING_MODEL", "mistral:7b"),  # Better for German
            "enabled": os.getenv("ENABLE_TEXT_PROCESSING", "true").lower() == "true",
        },
        
        # German-Optimized Models Configuration
        "german_models": {
            "primary": "phi3.5:3.8b",     # Best German accuracy (tested: Kafe->Kaffee)
            "secondary": "mistral:7b",     # Good German understanding
            "fallback": "llama3.2:3b",    # Basic German support
        },
        
        # Local Models Configuration
        "local_models": {
            "directory": os.getenv("LOCAL_MODELS_DIR", "./models"),
            "recommended_models": [
                "llama3",           # General purpose, good for most tasks
                "mistral",          # Fast and efficient
                "command-r",        # Good for structured tasks
                "aya",              # Multilingual, excellent for translation
                "codellama",        # Good for structured data like tables
                "phi3",             # Lightweight, good for simple tasks
            ]
        },
        
        # Audio Configuration
        "audio": {
            "sample_rate": int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            "channels": int(os.getenv("AUDIO_CHANNELS", "1")),
            "chunk_size": int(os.getenv("AUDIO_CHUNK_SIZE", "1024")),
            "record_seconds": int(os.getenv("AUDIO_RECORD_SECONDS", "30")),
            # Device IDs for sounddevice (input, output)
            "input_device": (int(env_input) if (env_input := os.getenv("AUDIO_INPUT_DEVICE")) else None),
            "output_device": (int(env_output) if (env_output := os.getenv("AUDIO_OUTPUT_DEVICE")) else None),
            # Professional audio interface settings
            "exclusive_mode": os.getenv("AUDIO_EXCLUSIVE_MODE", "false").lower() == "true",
            "custom_sample_rate": (int(env_sr) if (env_sr := os.getenv("AUDIO_CUSTOM_SAMPLE_RATE")) else None),
            "buffer_size": (int(env_buffer) if (env_buffer := os.getenv("AUDIO_BUFFER_SIZE")) else None),
            # Quality settings
            "bit_depth": int(os.getenv("AUDIO_BIT_DEPTH", "24")),  # 16, 24, or 32 bit
            "use_float32": os.getenv("AUDIO_USE_FLOAT32", "true").lower() == "true",
        },
        
        # Knowledge Base Configuration
        "knowledge": {
            "db_path": os.getenv("KNOWLEDGE_DB_PATH", "./data/knowledge.db"),
            "vector_db_path": os.getenv("VECTOR_DB_PATH", "./data/vectors"),
        },
        
        # Output Configuration
        "output": {
            "output_dir": os.getenv("OUTPUT_DIR", "./output"),
            "audio_output_dir": os.getenv("AUDIO_OUTPUT_DIR", "./output/audio"),
        },
        
        # Debug Configuration
        "debug": {
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        },
    }
    
    # Ensure directories exist
    Path(config["knowledge"]["db_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(config["knowledge"]["vector_db_path"]).mkdir(parents=True, exist_ok=True)
    Path(config["output"]["output_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["output"]["audio_output_dir"]).mkdir(parents=True, exist_ok=True)
    
    return config
