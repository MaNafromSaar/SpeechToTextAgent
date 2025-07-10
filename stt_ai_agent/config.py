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
        # Whisper Configuration
        "whisper": {
            "model": os.getenv("WHISPER_MODEL", "base"),
            "device": os.getenv("WHISPER_DEVICE", "cuda"),
            "language": os.getenv("WHISPER_LANGUAGE", "de"),
        },
        
        # Ollama Configuration
        "ollama": {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        },
        
        # Audio Configuration
        "audio": {
            "sample_rate": int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            "channels": int(os.getenv("AUDIO_CHANNELS", "1")),
            "chunk_size": int(os.getenv("AUDIO_CHUNK_SIZE", "1024")),
            "record_seconds": int(os.getenv("AUDIO_RECORD_SECONDS", "30")),
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
