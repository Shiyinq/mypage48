# Use Python 3.12.11 as the base image
FROM python:3.12.11-slim

# Install build tools & deps for pandas/numpy/scipy
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the entire requirements directory
COPY requirements /app/requirements

# Upgrade pip to the latest version ensuring better connectivity handling
RUN pip install --upgrade pip

# Install production dependencies
RUN pip install --no-cache-dir -r /app/requirements/prod.txt

# Copy the src directory contents into the container at /app/src
COPY src /app/src

# Copy scripts directory
COPY scripts /app/scripts

# Make it executable
RUN chmod +x /app/scripts/start-prod.sh

# Create log directory and set permissions so the app can write logs
RUN mkdir -p /var/log/fasmo && chmod 777 /var/log/fasmo

# Set the Python path to include the src directory
ENV PYTHONPATH=/app/src

# Expose port 8000 for the backend API
EXPOSE 8000

# Use the production start script as the container entrypoint
CMD ["/app/scripts/start-prod.sh"]