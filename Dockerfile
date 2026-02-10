FROM python:3.14-alpine AS builder

ENV PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apk add --no-cache \
    build-base \
    cargo \
    curl \
    freetype-dev \
    git \
    lcms2-dev \
    libffi-dev \
    libjpeg-turbo-dev \
    tiff-dev \
    linux-headers \
    openjpeg-dev \
    openssl-dev \
    pkgconf \
    postgresql-dev \
    rust \
    zlib-dev

WORKDIR /tmp/build
COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-compile --root /install -r requirements.txt && \
    pip install --no-compile --root /install granian[pname,uvloop]

FROM python:3.14-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apk add --no-cache \
    ca-certificates \
    freetype \
    lcms2 \
    libffi \
    libjpeg-turbo \
    libstdc++ \
    tiff \
    openjpeg \
    openssl \
    postgresql-libs \
    curl \
    tini \
    zlib

# Copy only the installed site-packages and console scripts from the builder
COPY --from=builder /install/usr/local /usr/local

# Runtime configuration
ARG API_WORKERS=4
ENV API_WORKERS=${API_WORKERS}

ARG API_THREADS_RUNTIME=2
ENV API_THREADS_RUNTIME=${API_THREADS_RUNTIME}

WORKDIR /keel
COPY . .

RUN python -m compileall -q app

STOPSIGNAL SIGTERM
ENTRYPOINT ["/sbin/tini", "--"]

CMD ["/bin/sh", "-c", "granian --host 0.0.0.0 --port 80 --interface asgi --workers ${API_WORKERS} --runtime-threads ${API_THREADS_RUNTIME} --loop uvloop --http 1 --backpressure 128 --respawn-failed-workers --access-log --process-name keel-worker --workers-kill-timeout 5 --workers-lifetime 43200 --workers-max-rss 512 app:api"]