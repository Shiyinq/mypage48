# Use Python 3.12.11 as the base image
FROM python:3.12.11-slim

# Install build tools & deps for pandas/numpy/scipy
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the entire requirements directory
COPY requirements /app/requirements

# Upgrade pip and install production dependencies using cache mounts
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r /app/requirements/prod.txt

# Copy the src directory contents into the container at /app/src
COPY src /app/src

# Copy the scraper directory
COPY scraper /app/scraper

# Copy scripts directory
COPY scripts /app/scripts

# Make scripts executable
RUN chmod +x /app/scripts/start-prod.sh /app/scripts/scraper-cron.sh

# Create log directory and set permissions so the app can write logs
RUN mkdir -p /var/log/mypage48 && chmod 777 /var/log/mypage48

# Set the Python path to include the src directory
ENV PYTHONPATH=/app/src

# Expose port 8080 for the backend API
EXPOSE 8080

# Use the production start script as the container entrypoint
CMD ["/app/scripts/start-prod.sh"]