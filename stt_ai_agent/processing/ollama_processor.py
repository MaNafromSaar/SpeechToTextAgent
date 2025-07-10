"""Ollama-based text processing functionality."""

import requests
import json
from typing import Dict, Any, Optional


class OllamaProcessor:
    """Ollama-based text processing and improvement."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama processor with configuration."""
        self.config = config
        self.base_url = config["ollama"]["base_url"]
        self.model = config["ollama"]["model"]
        
        # Prompt templates for different text formats
        self.prompts = {
            "improve": """Du bist ein professioneller deutscher Texteditor. Verbessere den folgenden Text:
- Korrigiere Grammatik- und Rechtschreibfehler
- Verbessere den Schreibstil und die Klarheit
- Behalte die ursprüngliche Bedeutung bei
- Antworte nur mit dem verbesserten Text

Text: {text}""",
            
            "email": """Wandle den folgenden Text in eine professionelle deutsche E-Mail um:
- Verwende eine angemessene Anrede und Schlussformel
- Strukturiere den Inhalt logisch
- Halte einen höflichen und professionellen Ton
- Antworte nur mit der E-Mail

Text: {text}""",
            
            "letter": """Wandle den folgenden Text in einen formellen deutschen Brief um:
- Verwende das korrekte Briefformat
- Füge Datum, Anrede und Schlussformel hinzu
- Strukturiere den Inhalt in Absätze
- Halte einen formellen Ton
- Antworte nur mit dem Brief

Text: {text}""",
            
            "table": """Erstelle eine übersichtliche Tabelle aus den Informationen im folgenden Text:
- Identifiziere die wichtigsten Datenpunkte
- Organisiere sie in logischen Spalten und Zeilen
- Verwende Markdown-Tabellenformat
- Antworte nur mit der Tabelle

Text: {text}""",
            
            "list": """Wandle den folgenden Text in eine strukturierte Liste um:
- Extrahiere die wichtigsten Punkte
- Organisiere sie hierarchisch wenn nötig
- Verwende Aufzählungszeichen oder Nummerierung
- Halte die Punkte prägnant
- Antworte nur mit der Liste

Text: {text}""",
            
            "translate_en": """Übersetze den folgenden deutschen Text ins Englische:
- Behalte die ursprüngliche Bedeutung und den Ton bei
- Verwende natürliches, idiomatisches Englisch
- Antworte nur mit der Übersetzung

Text: {text}""",
            
            "translate_fr": """Übersetze den folgenden deutschen Text ins Französische:
- Behalte die ursprüngliche Bedeutung und den Ton bei
- Verwende natürliches, idiomatisches Französisch
- Antworte nur mit der Übersetzung

Text: {text}"""
        }
    
    def process_text(self, text: str, format_type: str) -> str:
        """
        Process text using Ollama LLM.
        
        Args:
            text: Input text to process
            format_type: Type of processing (improve, email, letter, table, list, translate_en, translate_fr)
            
        Returns:
            Processed text
        """
        if format_type not in self.prompts:
            raise ValueError(f"Unknown format type: {format_type}")
        
        prompt = self.prompts[format_type].format(text=text)
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }
        }
        
        try:
            # Send request to Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Ollama response: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> list:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
            
        except requests.exceptions.RequestException:
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model to Ollama."""
        try:
            payload = {"name": model_name}
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=300  # 5 minutes for model download
            )
            return response.status_code == 200
            
        except requests.exceptions.RequestException:
            return False
