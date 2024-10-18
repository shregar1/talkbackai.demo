# Use Ubuntu as the base image
FROM ubuntu:22.04

# Set environment variables to avoid interaction prompts
ENV DEBIAN_FRONTEND=noninteractive
# Set the time zone
ENV TZ=Asia/Kolkata

# Install necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    ntp \
    libgl1-mesa-glx \
    portaudio19-dev \
    curl \
    wget \
    ffmpeg \
    flac \
    gcc \
    g++ \
    libsqlite3-dev\
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y python3 python3-pip libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Copy the requirements.txt first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Install transformers and langchain_google_genai separately
RUN pip3 install --no-cache-dir transformers==4.44.2
RUN pip3 install --no-cache-dir langchain_google_genai
RUN pip3 install faiss-cpu

# Copy the FastAPI application code to the container
COPY . /app

# Set the working directory
WORKDIR /app

# Expose the port FastAPI will run on
EXPOSE 8005

RUN mkdir -p /app/temp

RUN chmod -R 777 /app/temp

# Run the FastAPI app with Uvicorn
CMD ["python3", "app.py"]