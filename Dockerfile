# Multi-stage Dockerfile supporting Python simulation and C++ HElib execution
FROM python:3.10-slim AS base

# Install system dependencies (Graphviz for FSM diagrams, build-essential for C++ / math libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz \
    git \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency metadata and install requirements
COPY pyproject.toml Pipfile ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir "git+https://github.com/elliptic-shiho/primefac-fork.git" && \
    pip install --no-cache-dir matplotlib transitions gmpy2 graphviz bitstring progressbar2 tqdm pytest ruff

# Copy application source code
COPY . .

# Default command runs the main state machine simulation
CMD ["python", "main.py"]
