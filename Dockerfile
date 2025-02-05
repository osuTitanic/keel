FROM python:3.11-bullseye

# Installing/Updating system dependencies
RUN apt update -y
RUN apt install postgresql git curl ffmpeg libavcodec-extra -y

# Install rust toolchain
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /deck

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

CMD gunicorn \
        --access-logfile - \
        -b 0.0.0.0:80 \
        -w $WEB_WORKERS \
        -k uvicorn.workers.UvicornWorker \
        --max-requests 50000 \
        --max-requests-jitter 10000 \
        app:api