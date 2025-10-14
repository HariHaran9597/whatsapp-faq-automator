# Dockerfile (Simplified)

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install ONLY the system dependencies we absolutely need: ffmpeg and git.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Download and cache the Whisper model
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Copy your application's source code
COPY ./backend ./backend
COPY ./data ./data

# Make port 8000 available
EXPOSE 8000

# Define the command to run your app
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]