FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    wget \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    libasound2-dev \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy entire project into container for install
COPY . .

# Install Python dependencies in editable mode
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/data /app/output /app/config

# Set proper permissions
RUN chmod +x /app/entrypoint.sh 2>/dev/null || true

# Expose port for potential web interface
EXPOSE 8000

# Default command
CMD ["stt-agent", "--help"]
