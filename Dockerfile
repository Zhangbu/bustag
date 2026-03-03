FROM python:3.13-slim as base

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends --yes \
    build-essential \
    libpq-dev \
    cron \
    git \
    && rm -rf /var/lib/apt/lists/*

FROM base as build

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim as release

# Install runtime dependencies
RUN apt-get update && apt-get install --no-install-recommends --yes \
    cron \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from build stage
COPY --from=build /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

COPY requirements.txt .

# Create docker directory
RUN mkdir -p /app/docker

# Copy docker scripts
COPY docker/entry.sh /app/docker/

# Create log file
RUN touch /var/log/bustag.log

# Set permissions
RUN chmod 755 /app/docker/*.sh

EXPOSE 8000

LABEL maintainer="gxtrobot <gxtrobot@gmail.com>"
LABEL version="0.3.0"
LABEL description="Bustag - ML-based recommendation system"

CMD ["/app/docker/entry.sh"]