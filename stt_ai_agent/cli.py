"""Command-line interface for STT AI Agent."""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .config import load_config
from .audio.recorder import AudioRecorder
from .transcription.whisper_stt import WhisperSTT
from .processing.ollama_processor import OllamaProcessor
from .knowledge.knowledge_base import KnowledgeBase

app = typer.Typer(help="STT AI Agent - Local Speech-to-Text and Text Processing")
console = Console()


@app.command()
def record(
    duration: int = typer.Option(30, "--duration", "-d", help="Recording duration in seconds"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output audio file path"),
    model: str = typer.Option("base", "--model", "-m", help="Whisper model to use"),
    process_text: bool = typer.Option(True, "--process", help="Process transcribed text with LLM"),
    format_type: str = typer.Option("improve", "--format", "-f", help="Text format: improve, email, letter, table, list"),
) -> None:
    """Record audio, transcribe, and optionally process the text."""
    console.print(Panel.fit("🎤 Starting STT AI Agent", style="bold blue"))
    
    config = load_config()
    
    # Initialize components
    recorder = AudioRecorder(config)
    stt = WhisperSTT(config, model=model)
    processor = OllamaProcessor(config) if process_text else None
    
    try:
        # Record audio
        console.print(f"🔴 Recording for {duration} seconds...")
        audio_file = recorder.record(duration=duration, output_file=output_file)
        console.print(f"✅ Audio saved to: {audio_file}")
        
        # Transcribe
        console.print("🗣️ Transcribing audio...")
        transcription = stt.transcribe(audio_file)
        console.print(Panel(transcription, title="📝 Transcription", style="green"))
        
        # Process text if requested
        if processor and transcription.strip():
            console.print(f"🤖 Processing text (format: {format_type})...")
            processed_text = processor.process_text(transcription, format_type)
            console.print(Panel(processed_text, title=f"✨ Processed ({format_type})", style="blue"))
            
            # Save to knowledge base
            if typer.confirm("💾 Save to knowledge base?"):
                kb = KnowledgeBase(config)
                kb.save_entry(transcription, processed_text, format_type)
                console.print("✅ Saved to knowledge base")
                
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def transcribe(
    audio_file: str = typer.Argument(help="Path to audio file"),
    model: str = typer.Option("base", "--model", "-m", help="Whisper model to use"),
    language: str = typer.Option("de", "--language", "-l", help="Audio language"),
) -> None:
    """Transcribe an existing audio file."""
    console.print(Panel.fit("🗣️ Transcribing Audio File", style="bold blue"))
    
    config = load_config()
    stt = WhisperSTT(config, model=model)
    
    if not Path(audio_file).exists():
        console.print(f"❌ Audio file not found: {audio_file}", style="bold red")
        raise typer.Exit(1)
    
    try:
        console.print(f"🔄 Transcribing {audio_file}...")
        transcription = stt.transcribe(audio_file, language=language)
        console.print(Panel(transcription, title="📝 Transcription", style="green"))
        
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def process(
    text: str = typer.Argument(help="Text to process"),
    format_type: str = typer.Option("improve", "--format", "-f", help="Format: improve, email, letter, table, list"),
    save: bool = typer.Option(False, "--save", "-s", help="Save to knowledge base"),
) -> None:
    """Process text with LLM."""
    console.print(Panel.fit("🤖 Processing Text", style="bold blue"))
    
    config = load_config()
    processor = OllamaProcessor(config)
    
    try:
        console.print(f"🔄 Processing text (format: {format_type})...")
        processed_text = processor.process_text(text, format_type)
        console.print(Panel(processed_text, title=f"✨ Processed ({format_type})", style="blue"))
        
        if save:
            kb = KnowledgeBase(config)
            kb.save_entry(text, processed_text, format_type)
            console.print("✅ Saved to knowledge base")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def knowledge(
    action: str = typer.Argument(help="Action: list, search, add"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query or content to add"),
) -> None:
    """Manage knowledge base."""
    console.print(Panel.fit("🧠 Knowledge Base", style="bold blue"))
    
    config = load_config()
    kb = KnowledgeBase(config)
    
    try:
        if action == "list":
            entries = kb.list_entries()
            if entries:
                for entry in entries[:10]:  # Show last 10 entries
                    console.print(f"📄 {entry['timestamp']}: {entry['format_type']}")
            else:
                console.print("📭 No entries found")
                
        elif action == "search":
            if not query:
                console.print("❌ Search query required", style="bold red")
                raise typer.Exit(1)
            results = kb.search(query)
            for result in results:
                console.print(Panel(result['processed_text'], title=f"📄 {result['format_type']}", style="cyan"))
                
        elif action == "add":
            if not query:
                console.print("❌ Content required", style="bold red")
                raise typer.Exit(1)
            kb.save_entry(query, query, "manual")
            console.print("✅ Added to knowledge base")
            
        else:
            console.print("❌ Invalid action. Use: list, search, or add", style="bold red")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def setup() -> None:
    """Initialize the STT AI Agent environment."""
    console.print(Panel.fit("🔧 Setting up STT AI Agent", style="bold blue"))
    
    try:
        # Create directories
        directories = ["data", "output", "output/audio", "config"]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            console.print(f"📁 Created directory: {directory}")
        
        # Create .env if it doesn't exist
        env_file = Path(".env")
        if not env_file.exists():
            env_example = Path(".env.example")
            if env_example.exists():
                env_file.write_text(env_example.read_text())
                console.print("⚙️ Created .env file from template")
            else:
                console.print("⚠️ .env.example not found, create .env manually")
        
        # Initialize knowledge base
        config = load_config()
        kb = KnowledgeBase(config)
        kb.initialize()
        console.print("🧠 Initialized knowledge base")
        
        console.print("✅ Setup complete! Run 'stt-agent --help' to get started.")
        
    except Exception as e:
        console.print(f"❌ Setup error: {e}", style="bold red")
        raise typer.Exit(1)


@app.command("list-devices")
def list_devices() -> None:
    """List available audio input and output devices"""
    console.print(Panel.fit("🎧 Available Audio Devices", style="bold magenta"))
    import sounddevice as sd

    devices = sd.query_devices()
    input_devs = [d for d in devices if d['max_input_channels'] > 0]
    output_devs = [d for d in devices if d['max_output_channels'] > 0]

    console.print("[bold]Input Devices:[/bold]")
    for idx, dev in enumerate(input_devs):
        console.print(f"{dev['index']}: {dev['name']} (channels: {dev['max_input_channels']})")

    console.print("\n[bold]Output Devices:[/bold]")
    for idx, dev in enumerate(output_devs):
        console.print(f"{dev['index']}: {dev['name']} (channels: {dev['max_output_channels']})")

    console.print("\nUse environment variables AUDIO_INPUT_DEVICE and AUDIO_OUTPUT_DEVICE to set defaults.")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
