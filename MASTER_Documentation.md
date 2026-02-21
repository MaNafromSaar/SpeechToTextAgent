# keepITlocal.ai — Master Documentation

> **Version:** 1.0  
> **Status:** Active Development  
> **Last Updated:** 2026-02-21  
> **Repository:** [MaNafromSaar/SpeechToTextAgent](https://github.com/MaNafromSaar/SpeechToTextAgent)

---

## Table of Contents

1. [Project Vision & Goals](#1-project-vision--goals)
2. [Architecture Overview](#2-architecture-overview)
3. [Technology Stack](#3-technology-stack)
4. [Local Deployment Guide](#4-local-deployment-guide)
5. [Configuration Reference](#5-configuration-reference)
6. [Service API Reference](#6-service-api-reference)
7. [German Language Processing](#7-german-language-processing)
8. [Knowledge Base](#8-knowledge-base)
9. [Development Workflow](#9-development-workflow)
10. [Roadmap](#10-roadmap)
11. [Team Roles & Responsibilities](#11-team-roles--responsibilities)
12. [Supplementary Documents](#12-supplementary-documents)

---

## 1. Project Vision & Goals

**keepITlocal.ai** is a privacy-first, fully local AI-powered Speech-to-Text (STT) system designed for German-language users, freelancers, and small businesses.

### Core Principles
- **No cloud dependency** — all processing happens on the local machine
- **Privacy by design** — speech data never leaves the device
- **Modular microservices** — each component is independently deployable and replaceable
- **German-first** — optimised for German grammar, vocabulary, and style

### Short-Term Goals (Proof of Concept)
- ✅ Containerised microservices stack (Docker Compose)
- ✅ Whisper-based German speech-to-text
- ✅ Local LLM text correction via Ollama
- ✅ Persistent knowledge base (SQLite + ChromaDB)
- ✅ Web UI for recording and reviewing transcriptions

### Medium-Term Goals
- [ ] Voice activity detection to avoid silent-segment transcriptions
- [ ] Real-time streaming transcription
- [ ] Web dashboard with session history and export
- [ ] Scheduled tasks and calendar integration (ERP foundation)
- [ ] Multi-user support with per-user knowledge bases

### Long-Term Vision
Build a **fully-fledged local ERP assistant** for small businesses and freelancers — covering scheduling, task delegation, documentation, and communication — powered entirely by local AI models.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      keepITlocal.ai                         │
│                                                             │
│  ┌───────────────┐   ┌───────────────┐   ┌──────────────┐  │
│  │  Web UI       │   │  STT Core     │   │  Knowledge   │  │
│  │  (Port 8080)  │──▶│  (Port 8000)  │──▶│  Base        │  │
│  │  HTML/JS      │   │  FastAPI      │   │  (Port 8001) │  │
│  └───────────────┘   │  Whisper      │   │  ChromaDB    │  │
│                      │  Ollama client│   │  SQLite      │  │
│                      └──────┬────────┘   └──────────────┘  │
│                             │                               │
│                      ┌──────▼────────┐                      │
│                      │  Ollama       │                      │
│                      │  (Port 11434) │                      │
│                      │  llama3.1:8b  │                      │
│                      └───────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Port | Responsibility |
|---|---|---|
| **STT Core** | 8000 | Audio ingestion, Whisper transcription, Ollama text correction |
| **Knowledge Base** | 8001 | Store entries, semantic search, correction suggestions (RAG) |
| **Ollama** | 11434 | Local LLM inference (text correction, summarisation) |
| **Web UI** | 8080 | Browser-based recording interface and result display |

---

## 3. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| **Containerisation** | Docker + Docker Compose | GPU passthrough via NVIDIA Container Toolkit |
| **Speech-to-Text** | OpenAI Whisper | `openai-whisper` or `faster-whisper`; language = `de` |
| **Local LLM** | Ollama + Llama 3.1 8B | Best German correction quality; runs locally |
| **API Framework** | FastAPI | Async, automatic OpenAPI docs |
| **Vector DB** | ChromaDB 0.5.x | Semantic similarity search for RAG |
| **Relational DB** | SQLite 3.46+ | Lightweight, file-based knowledge store |
| **Web UI** | Vanilla HTML/JS | No build step required |
| **Python** | 3.10+ | Type hints throughout |

### Recommended Hardware
- CPU: 6+ cores (Ryzen 5 / Intel i5 or better)
- RAM: 16 GB minimum (32 GB recommended for llama3.1:8b)
- GPU: NVIDIA 8 GB VRAM or more (optional but recommended)
- Storage: 20 GB free (models + data)

---

## 4. Local Deployment Guide

### Prerequisites

1. **Docker Desktop** (Windows/macOS) or **Docker Engine + Docker Compose** (Linux)
2. **NVIDIA drivers** + **NVIDIA Container Toolkit** (for GPU support)
3. **Ollama** — download from [https://ollama.ai](https://ollama.ai)

### Step-by-Step Setup

#### 1. Clone the repository
```bash
git clone https://github.com/MaNafromSaar/SpeechToTextAgent.git
cd SpeechToTextAgent
```

#### 2. Configure the environment
```bash
cp .env.example .env
# Open .env in your editor and adjust:
#   WHISPER_MODEL, OLLAMA_MODEL, audio device settings
```

#### 3. Pull the Ollama model (first time only)
```bash
ollama pull llama3.1:8b
```

#### 4. Start all services
```bash
./start.sh
# or manually:
docker-compose up --build -d
```

#### 5. Verify health
```bash
python3 test_system.py
```

#### 6. Open the Web UI
Navigate to `http://localhost:8080` in your browser.

### Stopping the System
```bash
docker-compose down
```

### Rebuilding After Code Changes
```bash
docker-compose up --build -d
```

---

## 5. Configuration Reference

All configuration is via environment variables in the `.env` file.

### Whisper
| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL` | `base` | Model size: `tiny`, `base`, `small`, `medium`, `large` |
| `WHISPER_DEVICE` | `cuda` | Inference device: `cuda` or `cpu` |
| `WHISPER_LANGUAGE` | `de` | Source language code |

### Ollama
| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model name (must be pulled first) |

### Audio
| Variable | Default | Description |
|---|---|---|
| `AUDIO_SAMPLE_RATE` | `16000` | Sample rate in Hz |
| `AUDIO_CHANNELS` | `1` | Input channels (1 = mono) |
| `AUDIO_CHUNK_SIZE` | `1024` | Buffer chunk size |
| `AUDIO_RECORD_SECONDS` | `30` | Default recording duration |
| `AUDIO_BIT_DEPTH` | `24` | Bit depth (16 or 24) |
| `AUDIO_EXCLUSIVE_MODE` | `false` | Enable for ASIO/Core Audio interfaces |

See [docs/PROFESSIONAL_AUDIO_SETUP.md](docs/PROFESSIONAL_AUDIO_SETUP.md) for audio interface-specific settings.

### Knowledge Base
| Variable | Default | Description |
|---|---|---|
| `KNOWLEDGE_DB_PATH` | `./data/knowledge.db` | SQLite database path |
| `VECTOR_DB_PATH` | `./data/vectors` | ChromaDB storage path |

---

## 6. Service API Reference

### STT Core (http://localhost:8000)

Interactive documentation: http://localhost:8000/docs

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/transcribe` | `multipart/form-data` audio file | Transcribe + correct audio |
| `POST` | `/process-text` | `{"text": "..."}` | Correct raw text via Ollama |
| `GET` | `/knowledge/search?q=...` | — | Search knowledge base |
| `GET` | `/health` | — | Service health status |

### Knowledge Base (http://localhost:8001)

Interactive documentation: http://localhost:8001/docs

| Method | Path | Body | Description |
|---|---|---|---|
| `POST` | `/entries` | `{"text": "...", "metadata": {...}}` | Store a new entry |
| `GET` | `/entries?page=1&size=20` | — | Paginated entry list |
| `POST` | `/search` | `{"query": "...", "n": 5}` | Semantic search |
| `GET` | `/corrections/{text}` | — | Suggest corrections |
| `GET` | `/health` | — | Service health status |

---

## 7. German Language Processing

### Whisper Configuration for German

```bash
WHISPER_MODEL=small    # recommended balance of speed vs. accuracy for German
WHISPER_LANGUAGE=de
```

Larger models (`medium`, `large`) yield better accuracy on regional accents and technical vocabulary.

### Ollama Text Correction Prompt

The STT Core service uses the following prompt template (German-native):

```
Korrigiere den folgenden deutschen Text.
Verbessere nur Grammatik, Rechtschreibung und Satzstruktur.
Behalte den Inhalt, Stil und die Bedeutung bei:

{transcribed_text}

Korrigierter Text:
```

### Model Recommendation

Based on research (see [docs/RESEARCH_REPORT.md](docs/RESEARCH_REPORT.md)):

| Model | German Quality | Speed | Size |
|---|---|---|---|
| `llama3.1:8b` ⭐ | Excellent | ~85 s | 4.9 GB |
| `llama3.2:3b` | Good | ~19 s | 2.0 GB |
| `thinkverse/towerinstruct` | Poor | ~55 s | 3.8 GB |

**Recommendation:** Use `llama3.1:8b` for production. Use `llama3.2:3b` for faster iteration during development.

---

## 8. Knowledge Base

The knowledge base uses a hybrid storage strategy:

- **SQLite** — stores full text entries, timestamps, metadata
- **ChromaDB** — stores vector embeddings for semantic search

### How RAG Works Here

1. After each successful transcription + correction, the result is stored in the knowledge base.
2. When new text arrives, the KB is queried for similar previous entries.
3. Relevant past entries are included in the correction prompt as context.
4. Over time, the system learns domain-specific vocabulary and corrections.

### Backup

The data volumes are defined in `docker-compose.yml`. To back up:

```bash
docker-compose down
tar -czf backup-$(date +%Y%m%d).tar.gz ./data/
```

---

## 9. Development Workflow

### Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, deployable code |
| `develop` | Integration branch for features |
| `feature/<name>` | Individual feature development |
| `fix/<name>` | Bug fix branches |

### Running Tests

```bash
# Full system integration test
python3 test_system.py

# STT core unit tests
python3 test_server.py

# German model evaluation
python3 test_german_models.py

# ASR model comparison
python3 test_asr_models.py
```

### Code Style

```bash
pip install -e ".[dev]"
black .          # formatting
isort .          # import sorting
mypy .           # type checking
pytest           # unit tests
```

### Adding a New Feature

1. Create a feature branch: `git checkout -b feature/my-feature develop`
2. Implement changes with type hints and docstrings
3. Add or update tests
4. Run `black .` + `isort .` + `mypy .`
5. Open a pull request against `develop`

---

## 10. Roadmap

### Phase 1 — Local PoC ✅ (Current)
- [x] Containerised microservices (Docker Compose)
- [x] German Whisper transcription
- [x] Ollama LLM text correction
- [x] ChromaDB + SQLite knowledge base
- [x] Basic Web UI
- [x] Professional audio interface support (ASIO / JACK / Core Audio)

### Phase 2 — Team Collaboration (Next)
- [ ] GitHub Actions CI/CD pipeline
- [ ] Automated integration tests in CI
- [ ] Docker images published to GitHub Container Registry
- [ ] Contribution guidelines (`CONTRIBUTING.md`)
- [ ] Issue templates and PR templates

### Phase 3 — Feature Expansion
- [ ] Voice activity detection (VAD)
- [ ] Real-time streaming transcription (WebSockets)
- [ ] Session history dashboard
- [ ] Audio export (WAV, MP3)
- [ ] Multi-language support beyond German

### Phase 4 — ERP Foundation
- [ ] Calendar & scheduling module
- [ ] Task management and delegation
- [ ] Client/contact management
- [ ] Document generation (letters, invoices)
- [ ] Local email integration

---

## 11. Team Roles & Responsibilities

| Role | Responsibilities |
|---|---|
| **Project Lead** | Vision, roadmap, stakeholder communication |
| **Backend Developer** | STT Core, Knowledge Base services, APIs |
| **ML Engineer** | Whisper tuning, prompt engineering, model evaluation |
| **DevOps** | Docker, CI/CD, deployment scripts |
| **Frontend Developer** | Web UI, dashboard |
| **QA / Tester** | Test coverage, integration testing, documentation |

See [docs/PROJECT_TRACKING.md](docs/PROJECT_TRACKING.md) for current assignments and sprint progress.

---

## 12. Supplementary Documents

| Document | Location | Description |
|---|---|---|
| Development Log & Tracking | [docs/PROJECT_TRACKING.md](docs/PROJECT_TRACKING.md) | Sprints, meetings, decisions |
| Research Report | [docs/RESEARCH_REPORT.md](docs/RESEARCH_REPORT.md) | German model comparison results |
| Professional Audio Setup | [docs/PROFESSIONAL_AUDIO_SETUP.md](docs/PROFESSIONAL_AUDIO_SETUP.md) | ASIO / JACK / Core Audio guide |
| Legacy Project Notes | [docs/PROJECT_SUCCESS.md](docs/PROJECT_SUCCESS.md) | Original PoC completion notes |

---

*keepITlocal.ai — keeping your data where it belongs: on your machine.*
