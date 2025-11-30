# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_VERSION=20

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code first
COPY . .

# Build React app (after copying everything so we have the full context)
WORKDIR /app/frontend
RUN npm install && npm run build
WORKDIR /app

# Ensure the built React app is in place
RUN ls -la app/static/ || echo "Static directory check"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8081

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8081", "--timeout", "120", "app.main:app"]

