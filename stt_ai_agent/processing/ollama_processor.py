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
        self.fallback_model = config["ollama"].get("fallback_model", "phi3.5:3.8b")
        
        # German-optimized models in order of preference
        self.german_models = [
            "phi3.5:3.8b",     # Best German accuracy (tested: Kafe->Kaffee)
            "mistral:7b",      # Good German understanding
            "thinkverse/towerinstruct:latest",  # Previous default
            "llama3.2:3b"      # Basic fallback
        ]
        
        # Prompt templates for different text formats
        self.prompts = {
            "improve": """Korrigiere nur Rechtschreibung und Grammatik in diesem deutschen Text. Gib nur den korrigierten Text zurück.

Text: {text}

Korrigierter Text:""",
            
            "email": """Wandle den deutschen Text in eine deutsche Geschäfts-E-Mail um.

AUFGABE: Erstelle eine professionelle deutsche E-Mail:
- Beginne mit "Sehr geehrte Damen und Herren"
- Strukturiere den Inhalt in höfliche Absätze
- Schließe mit "Mit freundlichen Grüßen"
- Antworte NUR mit der deutschen E-Mail
- KEINE Erklärungen oder englischen Begriffe

Text: {text}""",
            
            "letter": """Wandle den deutschen Text in einen deutschen Geschäftsbrief um.

AUFGABE: Erstelle einen formellen deutschen Brief:
- Verwende korrektes deutsches Briefformat
- Beginne mit "Sehr geehrte Damen und Herren"
- Strukturiere professionell in Absätze
- Schließe mit "Mit freundlichen Grüßen"
- Antworte NUR mit dem deutschen Brief
- KEINE Erklärungen oder englischen Begriffe

Text: {text}""",
            
            "table": """Du sollst aus einem deutschen Text eine deutsche Tabelle erstellen.
ABSOLUTE REGEL: NIE ÜBERSETZEN! Nur deutsche Tabelle erstellen!

Erstelle eine übersichtliche Tabelle aus den Informationen im folgenden deutschen Text:
- Identifiziere die wichtigsten Datenpunkte
- Organisiere sie in logischen Spalten und Zeilen
- Verwende deutsche Spaltenüberschriften
- Verwende Markdown-Tabellenformat
- NIEMALS ins Englische übersetzen - immer auf Deutsch bleiben!
- Antworte nur mit der deutschen Tabelle

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
        Process text using Ollama LLM with German-optimized models.
        
        Args:
            text: Input text to process
            format_type: Type of processing (improve, email, letter, table, list, translate_en, translate_fr)
            
        Returns:
            Processed text
        """
        if format_type not in self.prompts:
            raise ValueError(f"Unknown format type: {format_type}")
        
        # Clear any previous conversation context
        self.clear_conversation()
        
        prompt = self.prompts[format_type].format(text=text)
        
        # Try German-optimized models in order of preference
        for model in self.german_models:
            try:
                # Prepare request payload with conversation isolation
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Lower temperature for more focused German responses
                        "top_p": 0.9,
                        "max_tokens": 1024,  # Shorter responses
                        "stop": ["<think>", "</think>", "**", "Rechtschreibfehler", "Worttrennungen", "Kurzum"],  # Stop on reasoning/explanation tokens
                        "num_ctx": 2048,     # Limited context window
                        "repeat_penalty": 1.1
                    },
                    # Force fresh conversation - no memory of previous requests
                    "context": None,
                    "keep_alive": "5m"  # Keep model loaded for efficiency
                }
                
                # Send request to Ollama
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=90
                )
                
                if response.status_code == 200:
                    result = response.json()
                    processed_text = result.get("response", "").strip()
                    
                    # Clean up the response to remove explanations and meta-commentary
                    cleaned_text = self._clean_german_response(processed_text)
                    
                    print(f"Text processed successfully with German model: {model}")
                    return cleaned_text
                else:
                    print(f"Model {model} returned status {response.status_code}")
                    continue
                    
            except Exception as e:
                print(f"Failed to process with German model {model}: {e}")
                continue
        
        # If all German models fail, return original text
        print("All German models failed, returning original text")
        return text
    
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
    
    def clear_conversation(self) -> bool:
        """Clear the model's conversation context to ensure fresh processing."""
        try:
            # Send a request to clear conversation state
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "",
                    "stream": False,
                    "keep_alive": "0s"
                },
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _clean_german_response(self, text: str) -> str:
        """Clean up German text response by removing explanations and meta-commentary."""
        import re
        
        # Remove explanations in parentheses
        text = re.sub(r'\s*\([^)]*Korrektur[^)]*\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\([^)]*Änderung[^)]*\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\([^)]*Hinzufügung[^)]*\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\([^)]*korrekter[^)]*\)', '', text, flags=re.IGNORECASE)
        
        # Remove long explanatory paragraphs that start with explanation keywords
        lines = text.split('\n')
        cleaned_lines = []
        skip_explanation = False
        
        for line in lines:
            line = line.strip()
            
            # Skip lines that are clearly explanations
            if any(keyword in line.lower() for keyword in [
                'korrektur:', 'erklärung:', 'verbesserung:', 'änderung:', 
                'begründung:', 'hinweis:', 'anmerkung:', 'grund:',
                'diese änderung', 'diese korrektur', 'verbessert durch'
            ]):
                skip_explanation = True
                continue
                
            # Skip lines that start with bullets or dashes (explanation lists)
            if line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                continue
                
            # Reset skip if we hit normal text again
            if line and not skip_explanation:
                cleaned_lines.append(line)
            elif line and len(line) > 50 and not any(keyword in line.lower() for keyword in [
                'korrektur', 'änderung', 'verbesserung', 'erklärung'
            ]):
                skip_explanation = False
                cleaned_lines.append(line)
        
        # Join and clean up extra whitespace
        cleaned_text = ' '.join(cleaned_lines)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # Remove any remaining meta-commentary
        cleaned_text = re.sub(r'\s*(?:Korrigierter Text:|Verbesserter Text:|Hier ist der korrigierte Text:)\s*', '', cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text
