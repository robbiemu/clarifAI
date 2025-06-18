# aclarai UI Service - Gradio Frontend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -e .

# Copy the service code
COPY . /app/

# Create a non-root user for security
RUN useradd -m -u 1000 aclarai && chown -R aclarai:aclarai /app
USER aclarai

# Expose the port that Gradio runs on (7860 is Gradio default)
EXPOSE 7860

# Health check (basic HTTP check on Gradio interface)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7860/ || exit 1

# Run the application
CMD ["python", "-m", "aclarai_ui.main"]