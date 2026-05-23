FROM python:3.11-slim

# Install Node.js 20 alongside Python
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies — separate layer so rebuilds skip this if requirements unchanged
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Node dependencies — separate layer so rebuilds skip this if package-lock unchanged
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci

# Build the Next.js static export into frontend/out/
COPY frontend/ frontend/
RUN cd frontend && npm run build

# Copy the backend source
COPY backend/ backend/

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
