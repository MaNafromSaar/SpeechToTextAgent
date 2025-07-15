FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies including professional audio support
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
    # Audio system libraries
    libasound2-dev \
    portaudio19-dev \
    pulseaudio \
    pulseaudio-utils \
    alsa-utils \
    alsa-base \
    jack-audio-connection-kit \
    libjack-jackd2-dev \
    ffmpeg \
    libsndfile1-dev \
    # Additional audio libraries for professional interfaces
    libportaudio2 \
    libportaudiocpp0 \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy only dependency files first for better layer caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies first (this layer will be cached unless dependencies change)
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (this will invalidate cache only when code changes)
COPY . .

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /app/data /app/output /app/config

# Set proper permissions
RUN chmod +x /app/entrypoint.sh 2>/dev/null || true

# Expose port for potential web interface
EXPOSE 8000

# Default command
CMD ["stt-agent", "--help"]
