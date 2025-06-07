# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first
RUN pip install --no-cache-dir gradio

# Copy the service directory
COPY . /app/

# Expose the port that Gradio runs on
EXPOSE 7860

# Run the application
CMD ["python", "-m", "clarifai_ui.main"]