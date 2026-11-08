# Use python:3.11-slim as the base image
FROM python:3.11-slim

# Install system dependencies: git and patch
# pytest and pip are part of the python environment or installed via pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    patch \
    && rm -rf /var/lib/apt/lists/*

# Install pytest using pip
RUN pip install --no-cache-dir pytest

# Set the working directory to /sandbox
WORKDIR /sandbox

# The application code will be cloned at runtime, so no COPY command is needed.
# Ensure the /sandbox directory is clean and ready.
CMD ["python3"]
