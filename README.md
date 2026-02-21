# keepITlocal.ai — Speech-to-Text Agent

A privacy-first, fully local Speech-to-Text AI agent with intelligent German text processing and a knowledge base — built as containerized microservices and designed to run entirely on your own machine. No cloud dependency required.

> **Project Status:** Active development — local deployment (proof of concept) → team project  
> See [MASTER_Documentation.md](MASTER_Documentation.md) for the full project roadmap and team guide.

## 🏗️ Architecture

The system is split into separate containerized services:

- **STT Core Service** (`stt-core/`) — Lightweight transcription and text processing
- **Knowledge Base Service** (`knowledge-service/`) — RAG learning and knowledge management
- **Ollama** — Local LLM for text correction and processing (runs 100 % locally)

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- NVIDIA GPU (optional, but recommended for Whisper)
- [Ollama](https://ollama.ai) installed locally

### 1. Clone & Configure
```bash
git clone https://github.com/MaNafromSaar/SpeechToTextAgent.git
cd SpeechToTextAgent
cp .env.example .env
# Edit .env to match your hardware and preferred models
```

### 2. Start the System
```bash
./start.sh
```

### 3. Verify Everything Works
```bash
python3 test_system.py
```

### 4. Access the Services
| Service | URL |
|---|---|
| STT Core API (Swagger) | http://localhost:8000/docs |
| Knowledge Base API (Swagger) | http://localhost:8001/docs |
| Ollama | http://localhost:11434 |

## 📡 API Endpoints

### STT Core Service (Port 8000)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/transcribe` | Upload audio for transcription + processing |
| `POST` | `/process-text` | Process text without transcription |
| `GET` | `/knowledge/search` | Search knowledge base |
| `GET` | `/health` | Service health check |

### Knowledge Base Service (Port 8001)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/entries` | Add new knowledge entry |
| `GET` | `/entries` | List entries with pagination |
| `POST` | `/search` | Semantic search |
| `GET` | `/corrections/{text}` | Get correction suggestions |
| `GET` | `/health` | Service health check |

## 🗂️ Project Structure

```
keepITlocal.ai/
├── stt-core/           # STT Core Service (FastAPI + Whisper + Ollama)
├── knowledge-service/  # Knowledge Base Service (ChromaDB + SQLite)
├── web/                # Web UI assets
├── docs/               # Supplementary documentation
├── .env.example        # Configuration template
├── docker-compose.yml  # Production stack
├── start.sh            # One-command startup
└── MASTER_Documentation.md  # Team guide & roadmap
```

## ⚙️ Configuration

Copy `.env.example` to `.env` and adjust for your setup:

```bash
# Whisper settings
WHISPER_MODEL=base        # tiny | base | small | medium | large
WHISPER_DEVICE=cuda       # cuda | cpu
WHISPER_LANGUAGE=de

# Ollama settings (local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b  # recommended for German language quality

# Audio settings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
```

## 🖥️ GPU Support

NVIDIA GPU acceleration is supported for:
- **Whisper** — faster speech transcription
- **Ollama** — LLM inference with GPU offload

See `docker-compose.yml` for the GPU resource reservation configuration.

## 🛠️ Local (Native) Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format & lint
black .
isort .
mypy .
```

## 📚 Documentation

| Document | Description |
|---|---|
| [MASTER_Documentation.md](MASTER_Documentation.md) | Full project guide, roadmap & team reference |
| [docs/PROJECT_TRACKING.md](docs/PROJECT_TRACKING.md) | Development log, meetings & workflow |
| [docs/RESEARCH_REPORT.md](docs/RESEARCH_REPORT.md) | Model comparison & research findings |
| [docs/PROFESSIONAL_AUDIO_SETUP.md](docs/PROFESSIONAL_AUDIO_SETUP.md) | ASIO / Core Audio / JACK setup guide |

## License

MIT License — see LICENSE file for details.
