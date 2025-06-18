# aclarai Core Service - Main Processing Engine
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the service code
COPY . /app/

# Install Python dependencies with trusted hosts for SSL issues
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -e .

# Install default prompt templates to /settings/prompts (make them available for user customization)
# /settings is mounted to the host, so users can access and modify these prompts
RUN mkdir -p /settings/prompts && python install/install_prompts.py --all --prompts-dir /settings/prompts

# Create a non-root user for security
RUN useradd -m -u 1000 aclarai && chown -R aclarai:aclarai /app
USER aclarai

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import aclarai_core; print('OK')" || exit 1

# Run the application
CMD ["python", "-m", "aclarai_core.main"]