# keepITlocal.ai — Project Tracking

> Live record of sprints, decisions, meetings, and workflow for the keepITlocal.ai project.  
> For the full project guide see [../MASTER_Documentation.md](../MASTER_Documentation.md).

---

## Table of Contents

1. [How to Use This Document](#how-to-use-this-document)
2. [Current Sprint](#current-sprint)
3. [Backlog](#backlog)
4. [Completed Work](#completed-work)
5. [Meeting Notes](#meeting-notes)
6. [Decisions Log](#decisions-log)
7. [Known Issues](#known-issues)

---

## How to Use This Document

- **Sprints** are time-boxed work periods (1–2 weeks). Add items to the current sprint or backlog.
- **Meeting Notes** should be appended chronologically.
- **Decisions Log** captures any significant architectural, tooling, or process decisions.
- Use `[x]` for completed tasks and `[ ]` for pending ones.
- Reference GitHub issues with `#<number>` where applicable.

---

## Current Sprint

### Sprint 1 — Local Deployment & Documentation (2026-02-21 → 2026-03-06)

**Goal:** Prepare the project for local single-machine deployment and hand it off to a small team.

#### Tasks

- [x] Migrate project documentation to `docs/` folder
- [x] Rename project branding to **keepITlocal.ai**
- [x] Update README.md for local-first deployment
- [x] Create MASTER_Documentation.md (team guide + roadmap)
- [x] Create this tracking document
- [ ] Verify Docker Compose stack starts cleanly on a fresh Linux machine
- [ ] Pull and test `llama3.1:8b` model via Ollama
- [ ] Run `test_system.py` end-to-end and fix any failures
- [ ] Add `CONTRIBUTING.md` with contribution guidelines
- [ ] Set up GitHub Actions workflow for basic CI (lint + tests)

#### Sprint Owner
@MaNafromSaar

---

## Backlog

### High Priority

- [ ] **VAD (Voice Activity Detection)** — Prevent silent-segment transcriptions from being processed
- [ ] **Streaming transcription** — Real-time WebSocket-based transcription endpoint
- [ ] **Session history UI** — Dashboard showing past transcription sessions with search
- [ ] **CI/CD pipeline** — GitHub Actions: lint, test, build Docker images, push to GHCR
- [ ] **Contribution guidelines** — `CONTRIBUTING.md` with branch strategy, PR template

### Medium Priority

- [ ] **faster-whisper integration** — Replace `openai-whisper` with `faster-whisper` for 2–4× speedup
- [ ] **Multi-stage correction pipeline** — Chain multiple prompts for complex corrections
- [ ] **Export functionality** — Export transcriptions as TXT, PDF, DOCX
- [ ] **Audio export** — Save recordings as WAV / MP3
- [ ] **User feedback loop** — Allow users to flag incorrect corrections to improve the KB

### Low Priority / Future

- [ ] **Multi-language support** — Extend beyond German (French, English)
- [ ] **Calendar integration** — Schedule meetings and tasks from voice commands
- [ ] **Task management module** — Local ERP foundation: tasks, delegation, deadlines
- [ ] **Client/contact management** — CRM basics for freelancers
- [ ] **Document generation** — Generate letters, invoices from templates + voice input
- [ ] **Local email integration** — Send summaries via local mail client

---

## Completed Work

### Pre-Sprint (Initial Development — Jul 2025)

- [x] Project inception and architecture design
- [x] Containerised microservices stack (Docker Compose)
- [x] STT Core Service with FastAPI + OpenAI Whisper
- [x] Knowledge Base Service with ChromaDB + SQLite 3.46.1
- [x] Ollama integration for local LLM text correction
- [x] Web UI for browser-based audio recording
- [x] Professional audio interface support (ASIO, JACK, Core Audio)
- [x] German model evaluation: selected `llama3.1:8b` as primary correction model
- [x] `.env` configuration system with example file
- [x] VS Code launch configurations and tasks
- [x] Research report: German model comparison (see [RESEARCH_REPORT.md](RESEARCH_REPORT.md))

---

## Meeting Notes

### 2026-02-21 — Project Kickoff / Transition to Team

**Attendees:** @MaNafromSaar (Project Lead)  
**Format:** Solo planning session

**Summary:**
- Reviewed current state: working local PoC on single machine
- Decided to transition project to team collaboration on GitHub
- Agreed on rebranding: project is now **keepITlocal.ai**
- Removed references to prior internal project name ("AIHAx") and decommissioned server infrastructure
- Identified key pending tasks for Sprint 1 (see above)
- Documentation restructured: secondary docs moved to `docs/` folder

**Action Items:**
- [ ] @MaNafromSaar — Invite team members to GitHub repository
- [ ] @MaNafromSaar — Set up GitHub Projects board for sprint tracking
- [ ] All — Review MASTER_Documentation.md and add feedback as GitHub issues

---

## Decisions Log

| Date | Decision | Rationale | Decision Maker |
|---|---|---|---|
| 2025-07-13 | Use `llama3.1:8b` as primary text correction model | Best German grammar quality in comparative testing; see RESEARCH_REPORT.md | @MaNafromSaar |
| 2025-07-13 | Microservices architecture (STT Core + KB separate) | Independent scaling, easier replacement of individual components | @MaNafromSaar |
| 2025-07-13 | SQLite + ChromaDB hybrid knowledge store | SQLite for structured data, ChromaDB for semantic search (RAG) | @MaNafromSaar |
| 2026-02-21 | Rename project to **keepITlocal.ai** | Clearer branding reflecting the local-first, privacy-first philosophy | @MaNafromSaar |
| 2026-02-21 | Move secondary docs to `docs/` folder | Keep repository root clean; README + MASTER_Documentation.md at root | @MaNafromSaar |

---

## Known Issues

| # | Description | Severity | Status |
|---|---|---|---|
| 1 | `llama3.2:3b` fails to correct "Kratuliert" → "gratuliert" | Medium | Open — mitigated by using `llama3.1:8b` |
| 2 | ASIO drivers not available inside Linux containers | Low | By design — use native installation for professional audio |
| 3 | ChromaDB requires SQLite ≥ 3.35; system SQLite may be older | Medium | Workaround: custom-compiled SQLite in Dockerfile.kb |
| 4 | No voice activity detection — silent segments are transcribed | Medium | Planned for Sprint 2 |

---

*Last updated: 2026-02-21*
