# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies
# FINAL FIX: Added 'build-essential' which includes the GCC compiler
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download and cache the Whisper model during the build process
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Copy your application's source code into the container
COPY ./backend ./backend
COPY ./data ./data

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run your app using uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]