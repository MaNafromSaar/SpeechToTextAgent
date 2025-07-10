# STT AI Agent

A local AI agent for German speech-to-text transcription, intelligent text processing, and knowledge base management.

## Features

- 🎤 **Audio Capture**: Record microphone input with high-quality audio processing
- 🗣️ **German STT**: Transcribe German speech using Whisper (local processing)
- 📝 **Text Transformation**: Convert transcriptions into various formats (email, letter, flowtext, table, list)
- ✏️ **Intelligent Revision**: Grammar fixes, style improvements, and better phrasing suggestions
- 🌍 **Translation**: Optional translation to French or English
- 🧠 **Knowledge Base**: Growing knowledge repository with manual addition capability
- 🐳 **Containerized**: Docker support to avoid Python dependency hell
- 🚀 **GPU Accelerated**: CUDA support for faster processing

## Quick Start

### Prerequisites

- WSL2 Ubuntu with NVIDIA drivers (for GPU support)
- Docker with NVIDIA Container Toolkit
- Python 3.10+ (for local development)

### Using Docker (Recommended)

```bash
# Build the container
docker-compose up --build

# Run STT agent
docker-compose exec stt-agent stt-agent --help
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the agent
stt-agent --help
```

## Architecture

```
stt_ai_agent/
├── audio/          # Audio capture and processing
├── transcription/  # Whisper STT integration
├── processing/     # LLM text processing with Ollama
├── knowledge/      # Knowledge base management
├── utils/          # Shared utilities
└── cli/            # Command-line interface
```

## GPU Support

This project supports NVIDIA GPUs for:
- **Whisper**: Faster speech transcription
- **Ollama**: Local LLM processing with GPU acceleration

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Whisper settings
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_DEVICE=cuda  # cuda, cpu

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Audio settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
```

## Development

```bash
# Setup development environment
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy .
```

## License

MIT License - see LICENSE file for details.
