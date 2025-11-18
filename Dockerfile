FROM python:3.14-alpine AS builder

ENV PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

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

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-compile --root /install -r requirements.txt

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
ARG WEB_WORKERS=4
ENV WEB_WORKERS=${WEB_WORKERS} \
    API_WORKERS=${WEB_WORKERS}

WORKDIR /keel
COPY . .

RUN python -m compileall -q app

STOPSIGNAL SIGTERM
ENTRYPOINT ["/sbin/tini", "--"]

CMD ["/bin/sh", "-c", "gunicorn --access-logfile - --preload -b 0.0.0.0:80 -w ${WEB_WORKERS} -k uvicorn.workers.UvicornWorker --max-requests 50000 --max-requests-jitter 10000 --graceful-timeout 5 --timeout 10 app:api"]