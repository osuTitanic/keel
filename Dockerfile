FROM python:3.13-slim-bullseye AS builder

# Installing build dependencies
RUN apt update -y && \
    apt install -y --no-install-recommends \
        postgresql-client \
        git \
        curl \
        build-essential \
        gcc \
        python3-dev \
        libpcre3-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install rust toolchain
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install python dependencies
# & gunicorn for deployment
WORKDIR /keel
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

FROM python:3.13-slim-bullseye

# Installing runtime dependencies
RUN apt update -y && \
    apt install -y --no-install-recommends \
        libpcre3-dev libssl-dev tini curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local /usr/local

# Disable output buffering
ENV PYTHONUNBUFFERED=1

# Get config for deployment
ARG API_WORKERS=4
ENV API_WORKERS $API_WORKERS

# Copy source code
COPY . .

# Generate __pycache__ directories
ENV PYTHONDONTWRITEBYTECODE=1
RUN python -m compileall -q app

STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD gunicorn \
    --access-logfile - \
    --preload \
    -b 0.0.0.0:80 \
    -w $WEB_WORKERS \
    -k uvicorn.workers.UvicornWorker \
    --max-requests 50000 \
    --max-requests-jitter 10000 \
    --graceful-timeout 5 \
    --timeout 10 \
    app:api