FROM python:3.13-slim-bullseye

# Installing/Updating system dependencies
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

WORKDIR /keel

# Install gunicorn for deployment
RUN pip install gunicorn

# Install python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Get config for deployment
ARG API_WORKERS=4
ENV API_WORKERS $API_WORKERS

# Generate __pycache__ directories
ENV PYTHONDONTWRITEBYTECODE=1
RUN python -m compileall -q app

# Disable output buffering
ENV PYTHONUNBUFFERED=1

CMD gunicorn \
        --access-logfile - \
        --preload \
        -b 0.0.0.0:80 \
        -w $WEB_WORKERS \
        -k uvicorn.workers.UvicornWorker \
        --max-requests 50000 \
        --max-requests-jitter 10000 \
        app:api