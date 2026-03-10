# Crypto Trading Bot Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY config/ config/
COPY core/ core/
COPY orderflow/ orderflow/
COPY strategy/ strategy/
COPY ai/ ai/
COPY database/ database/
COPY paper_trading/ paper_trading/
COPY dashboard/ dashboard/
COPY main.py .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p logs data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CRYPTOBOT_LOGGING__LEVEL=INFO

# Expose dashboard port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]

