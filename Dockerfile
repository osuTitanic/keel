FROM python:3.14-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Install build dependencies only in the builder stage
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libpq-dev \
        libssl-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install rust toolchain for pyo3/orjson wheels
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /tmp/build
COPY requirements.txt ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-compile --root /install -r requirements.txt

FROM python:3.14-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime-only dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        libssl3 \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Copy only the installed site-packages and console scripts from the builder
COPY --from=builder /install/usr/local /usr/local

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Runtime configuration
ARG WEB_WORKERS=4
ENV WEB_WORKERS=${WEB_WORKERS} \
    API_WORKERS=${WEB_WORKERS}

# Copy source code
WORKDIR /keel
COPY . .

# Precompile python files for faster startup
RUN python -m compileall -q app

STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["/bin/sh", "-c", "gunicorn --access-logfile - --preload -b 0.0.0.0:80 -w ${WEB_WORKERS} -k uvicorn.workers.UvicornWorker --max-requests 50000 --max-requests-jitter 10000 --graceful-timeout 5 --timeout 10 app:api"]