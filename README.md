# STT AI Agent - Containerized Microservices

A sophisticated Speech-to-Text AI agent with intelligent text processing and learning capabilities, built as containerized microservices for better scalability and deployment flexibility.

## 🏗️ Architecture

The system is now split into separate containerized services:

- **STT Core Service** (`stt-core/`) - Lightweight transcription and text processing
- **Knowledge Base Service** (`knowledge-service/`) - RAG learning and knowledge management  
- **Ollama** - Local LLM for text correction and processing

## � Quick Start

1. **Start the system:**
   ```bash
   ./start.sh
   ```

2. **Test the system:**
   ```bash
   python3 test_system.py
   ```

3. **Access the services:**
   - STT Core API: http://localhost:8000/docs
   - Knowledge Base API: http://localhost:8001/docs
   - Ollama: http://localhost:11434

## 📡 API Endpoints

### STT Core Service (Port 8000)
- `POST /transcribe` - Upload audio file for transcription and processing
- `POST /process-text` - Process text without transcription
- `GET /knowledge/search` - Search knowledge base through STT service
- `GET /health` - Service health check

### Knowledge Base Service (Port 8001)  
- `POST /entries` - Add new knowledge entry
- `GET /entries` - List entries with pagination
- `POST /search` - Semantic search through knowledge base
- `GET /corrections/{text}` - Get correction suggestions
- `GET /health` - Service health check
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
