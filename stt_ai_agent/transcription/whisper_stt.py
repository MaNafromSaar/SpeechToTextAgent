"""Whisper speech-to-text functionality."""

import whisper
from pathlib import Path
from typing import Dict, Any, Optional, List


class WhisperSTT:
    """Whisper-based speech-to-text transcription."""
    
    def __init__(self, config: Dict[str, Any], model: str = None):
        """Initialize Whisper STT with configuration."""
        self.config = config
        self.model_name = model or config["whisper"]["model"]
        self.device = config["whisper"]["device"]
        self.language = config["whisper"]["language"]
        
        # Use openai-whisper for now (faster-whisper needs newer Python)
        self.model = whisper.load_model(self.model_name, device=self.device)
    
    def transcribe(
        self, 
        audio_file: str, 
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: Path to audio file
            language: Optional language override
            
        Returns:
            Transcribed text
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Use provided language or default
        target_language = language or self.language
        
        # Transcribe using openai-whisper
        result = self.model.transcribe(
            str(audio_path),
            language=target_language
        )
        
        return result["text"].strip()
    
    def transcribe_with_timestamps(
        self, 
        audio_file: str, 
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe with timestamp information.
        
        Args:
            audio_file: Path to audio file
            language: Optional language override
            
        Returns:
            List of segments with timestamps
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Use provided language or default
        target_language = language or self.language
        
        # Transcribe using openai-whisper
        result = self.model.transcribe(
            str(audio_path),
            language=target_language
        )
        
        # Return segments with timestamps
        segments = []
        for segment in result["segments"]:
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            })
        
        return segments
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models."""
        return [
            "tiny", "tiny.en",
            "base", "base.en", 
            "small", "small.en",
            "medium", "medium.en",
            "large-v1", "large-v2", "large-v3"
        ]
