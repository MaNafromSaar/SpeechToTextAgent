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

    # Get all devices and host APIs
    devices = sd.query_devices()
    host_apis = sd.query_hostapis()
    
    # Create mapping of host API index to name and type
    host_api_info = {}
    for api in host_apis:
        api_type = api['name']
        is_professional = any(pro_type in api_type.upper() for pro_type in ['ASIO', 'CORE AUDIO', 'JACK'])
        host_api_info[api['index']] = {
            'name': api_type,
            'is_professional': is_professional,
            'device_count': api['device_count']
        }

    input_devs = [d for d in devices if d['max_input_channels'] > 0]
    output_devs = [d for d in devices if d['max_output_channels'] > 0]

    def format_device_info(dev):
        host_info = host_api_info.get(dev['hostapi'], {'name': 'Unknown', 'is_professional': False})
        api_name = host_info['name']
        pro_indicator = " 🎛️" if host_info['is_professional'] else ""
        latency_info = f" (Low: {dev.get('default_low_input_latency', 0):.3f}s)" if dev.get('default_low_input_latency') else ""
        return f"{dev['index']}: {dev['name']} [{api_name}]{pro_indicator} (ch: {dev.get('max_input_channels', dev.get('max_output_channels', 0))}){latency_info}"

    console.print("[bold]Input Devices:[/bold]")
    for dev in input_devs:
        console.print(format_device_info(dev))

    console.print("\n[bold]Output Devices:[/bold]")
    for dev in output_devs:
        console.print(format_device_info(dev))

    # Show professional audio interfaces separately
    pro_devices = [d for d in devices if host_api_info.get(d['hostapi'], {}).get('is_professional', False)]
    ssl2_devices = [d for d in devices if 'SSL' in d['name'].upper() or 'SSL2' in d['name'].upper()]
    
    if ssl2_devices:
        console.print("\n[bold green]🎛️ SSL2 ASIO Interface Detected:[/bold green]")
        for dev in ssl2_devices:
            channels_in = dev.get('max_input_channels', 0)
            channels_out = dev.get('max_output_channels', 0)
            api_name = host_api_info[dev['hostapi']]['name']
            latency = dev.get('default_low_input_latency', 0)
            console.print(f"  ✅ {dev['index']}: {dev['name']} [{api_name}]")
            console.print(f"     📥 Inputs: {channels_in} | 📤 Outputs: {channels_out} | ⚡ Latency: {latency:.3f}s")
    
    if pro_devices and not ssl2_devices:
        console.print("\n[bold cyan]🎛️ Professional Audio Interfaces:[/bold cyan]")
        for dev in pro_devices:
            channels = max(dev.get('max_input_channels', 0), dev.get('max_output_channels', 0))
            api_name = host_api_info[dev['hostapi']]['name']
            console.print(f"  {dev['index']}: {dev['name']} [{api_name}] ({channels} channels)")

    console.print("\n[bold]Host APIs Available:[/bold]")
    for api in host_apis:
        pro_indicator = " 🎛️" if any(pro_type in api['name'].upper() for pro_type in ['ASIO', 'CORE AUDIO', 'JACK']) else ""
        asio_indicator = " 🚀" if 'ASIO' in api['name'].upper() else ""
        console.print(f"  {api['name']}{pro_indicator}{asio_indicator} ({api['device_count']} devices)")

    # SSL2 specific recommendations
    if ssl2_devices:
        console.print("\n[bold green]💡 SSL2 Recommendations:[/bold green]")
        console.print("  • Use ASIO driver for lowest latency")
        console.print("  • Set buffer size: 128-256 samples")
        console.print("  • Sample rate: 44.1kHz or 48kHz")
        console.print("  • Enable direct monitoring if available")
        console.print("  • Use 'stt-agent configure-audio --ssl2' for quick setup")
    
    console.print("\nUse environment variables AUDIO_INPUT_DEVICE and AUDIO_OUTPUT_DEVICE to set defaults.")
    console.print("🎛️ = Professional | 🚀 = ASIO Support")


@app.command("configure-audio")
def configure_audio(
    ssl2: bool = typer.Option(False, "--ssl2", help="Configure for SSL2 ASIO interface"),
    device_id: Optional[int] = typer.Option(None, "--device", "-d", help="Audio device ID"),
    sample_rate: int = typer.Option(44100, "--rate", "-r", help="Sample rate (Hz)"),
    buffer_size: int = typer.Option(128, "--buffer", "-b", help="Buffer size (samples)"),
    test: bool = typer.Option(False, "--test", "-t", help="Test configuration after setup"),
) -> None:
    """Configure audio settings for optimal performance"""
    
    try:
        import sounddevice as sd
        import numpy as np
        import os
        from pathlib import Path
    except ImportError as e:
        console.print(f"❌ Import error: {e}")
        console.print("Please ensure sounddevice and numpy are installed")
        return
    
    if ssl2:
        console.print("[bold green]🎛️ Configuring for SSL2 ASIO Interface[/bold green]")
        
        # Check if SSL2 config exists
        ssl2_config = Path(".env.ssl2")
        if ssl2_config.exists():
            console.print("✅ Loading SSL2 configuration...")
            
        # Detect SSL2 device
        devices = sd.query_devices()
        ssl2_device = None
        for i, dev in enumerate(devices):
            if 'SSL' in dev['name'].upper() or 'SSL2' in dev['name'].upper():
                ssl2_device = dev
                device_id = i
                break
        
        if ssl2_device:
            console.print(f"✅ SSL2 detected: {ssl2_device['name']} (Device ID: {device_id})")
            console.print(f"   📥 Inputs: {ssl2_device.get('max_input_channels', 0)}")
            console.print(f"   📤 Outputs: {ssl2_device.get('max_output_channels', 0)}")
            
            # Set environment variables for this session
            os.environ['AUDIO_INPUT_DEVICE'] = str(device_id)
            os.environ['AUDIO_OUTPUT_DEVICE'] = str(device_id)
            os.environ['PREFERRED_AUDIO_INTERFACE'] = 'SSL2'
            os.environ['ASIO_BUFFER_SIZE'] = str(buffer_size)
            os.environ['AUDIO_SAMPLE_RATE'] = str(sample_rate)
            
            console.print(f"✅ Configuration set:")
            console.print(f"   🎚️ Sample Rate: {sample_rate} Hz")
            console.print(f"   📊 Buffer Size: {buffer_size} samples")
            console.print(f"   🎛️ Device: {ssl2_device['name']}")
            
        else:
            console.print("❌ SSL2 interface not detected!")
            console.print("💡 Make sure:")
            console.print("   • SSL2 is connected via USB")
            console.print("   • ASIO drivers are installed")
            console.print("   • Device is powered on")
            return
    
    else:
        # Generic audio configuration
        if device_id is not None:
            devices = sd.query_devices()
            if device_id < len(devices):
                device = devices[device_id]
                console.print(f"✅ Configuring device: {device['name']}")
                os.environ['AUDIO_INPUT_DEVICE'] = str(device_id)
                os.environ['AUDIO_OUTPUT_DEVICE'] = str(device_id)
            else:
                console.print(f"❌ Device ID {device_id} not found!")
                return
        else:
            console.print("❌ Please specify --device or use --ssl2 for automatic SSL2 setup")
            return
    
    if test:
        console.print("\n🧪 Testing audio configuration...")
        try:
            # Quick audio test
            test_duration = 1.0
            fs = sample_rate
            
            # Test recording
            console.print("🎤 Testing recording (1 second)...")
            recording = sd.rec(int(test_duration * fs), samplerate=fs, channels=1, device=device_id)
            sd.wait()
            
            # Test playback
            console.print("🔊 Testing playback...")
            sd.play(recording, samplerate=fs, device=device_id)
            sd.wait()
            
            console.print("✅ Audio test completed successfully!")
            
        except Exception as e:
            console.print(f"❌ Audio test failed: {e}")
            console.print("💡 Try adjusting buffer size or checking device permissions")


@app.command("test-audio")
def test_audio(
    duration: int = typer.Option(5, "--duration", "-d", help="Test recording duration in seconds"),
    device_id: Optional[int] = typer.Option(None, "--device", help="Audio input device ID to test"),
) -> None:
    """Test audio recording with specified or default device."""
    console.print(Panel.fit("🎤 Audio Device Test", style="bold cyan"))
    
    import sounddevice as sd
    import numpy as np
    
    try:
        if device_id is not None:
            # Test specific device
            device_info = sd.query_devices(device_id)
            console.print(f"Testing device {device_id}: {device_info['name']}")
            
            # Set the device temporarily
            original_device = sd.default.device
            sd.default.device = device_id
        else:
            device_info = sd.query_devices(sd.default.device)
            console.print(f"Testing default device: {device_info}")
        
        # Record test audio
        console.print(f"🔴 Recording for {duration} seconds...")
        sample_rate = 16000
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        
        # Analyze recording
        max_amplitude = np.max(np.abs(recording))
        rms_level = np.sqrt(np.mean(recording**2))
        
        console.print(f"✅ Recording completed")
        console.print(f"📊 Max amplitude: {max_amplitude:.4f}")
        console.print(f"📊 RMS level: {rms_level:.4f}")
        
        if max_amplitude < 0.001:
            console.print("⚠️  Very low audio level - check microphone connection", style="bold yellow")
        elif max_amplitude > 0.9:
            console.print("⚠️  Audio level very high - may be clipping", style="bold yellow")
        else:
            console.print("✅ Audio levels look good!", style="bold green")
        
        # Restore original device if we changed it
        if device_id is not None:
            sd.default.device = original_device
            
    except Exception as e:
        console.print(f"❌ Audio test failed: {e}", style="bold red")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
