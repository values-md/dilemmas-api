# Dockerfile for VALUES.md Dilemmas API
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY seeds/ ./seeds/
COPY config.yaml .

# Install dependencies
RUN uv sync --frozen

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8080

# Run entrypoint (migrations + server)
ENTRYPOINT ["./entrypoint.sh"]
