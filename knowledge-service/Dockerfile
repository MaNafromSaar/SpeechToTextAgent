FROM python:3.10-slim

# Install system dependencies including newer SQLite
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install newer SQLite
WORKDIR /tmp
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-3460100.tar.gz \
    && tar -xzf sqlite-autoconf-3460100.tar.gz \
    && cd sqlite-autoconf-3460100 \
    && ./configure --prefix=/usr/local \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd / && rm -rf /tmp/sqlite-autoconf-3460100*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy knowledge base code
COPY knowledge_base.py .
COPY api.py .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8001

# Set environment variables
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV PYTHONPATH=/app

# Run the knowledge base service
CMD ["python", "api.py"]
