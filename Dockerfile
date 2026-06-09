FROM python:3.11-slim

# Install Node.js (required by yt-dlp EJS solver) and ffmpeg for merging
# Uses NodeSource setup script to get a modern Node release
RUN apt-get update \
    && apt-get install -y curl ca-certificates gnupg --no-install-recommends \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs ffmpeg --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads

# BASE_URL should be set at runtime, e.g. https://myapp.onrender.com
ENV PORT=5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
