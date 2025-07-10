<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# STT AI Agent - Copilot Instructions

This is a local AI agent project for German speech-to-text transcription, text processing, and knowledge base management.

## Project Structure

- **stt_ai_agent/**: Main package directory
  - **audio/**: Audio capture and recording functionality
  - **transcription/**: Whisper-based speech-to-text
  - **processing/**: Ollama LLM text processing
  - **knowledge/**: Knowledge base with SQLite and ChromaDB
  - **cli.py**: Command-line interface using Typer

## Key Technologies

- **Python 3.10+** with modern type hints
- **Whisper** (faster-whisper) for German STT
- **Ollama** for local LLM text processing
- **Docker** with GPU support (NVIDIA)
- **SQLite** + **ChromaDB** for knowledge storage
- **Typer** + **Rich** for CLI interface

## Coding Guidelines

1. **Type Hints**: Always use type hints for function parameters and return values
2. **Error Handling**: Use proper exception handling with informative error messages
3. **Configuration**: Use the config system for all settings (no hardcoded values)
4. **German Language**: Text processing prompts are in German for native processing
5. **GPU Support**: Consider CUDA availability for Whisper and potential Ollama acceleration
6. **Docker First**: Prioritize containerized solutions to avoid dependency hell

## Architecture Patterns

- **Dependency Injection**: Pass config objects to classes
- **Factory Pattern**: Use for model initialization (Whisper, Ollama)
- **Repository Pattern**: Knowledge base abstracts storage details
- **Command Pattern**: CLI commands are self-contained

## Docker & GPU

- Use `nvidia/cuda:12.1-runtime-ubuntu22.04` base image
- Include NVIDIA Container Toolkit support
- Mount volumes for data persistence
- Support both CPU and GPU execution paths

## Environment Variables

All configuration through `.env` file:
- Whisper model selection and device
- Ollama URL and model configuration
- Audio settings and quality
- Knowledge base paths
- Debug and logging levels

## German Language Support

- Default language is German ("de")
- Prompts for text processing are in German
- Support for translation to English/French
- Consider German-specific grammar and style rules

When suggesting code improvements or new features, prioritize:
1. Maintaining the containerized approach
2. Proper error handling and logging
3. German language optimization
4. GPU acceleration where applicable
5. Type safety and modern Python practices
