# ==============================================================================
# DOCKERFILE - CONTAINERIZATION GUIDE
# ==============================================================================
#
# PURPOSE:
#   Define how to build a Docker image that packages:
#   - Python 3.10 runtime
#   - All Python dependencies
#   - Application code
#   - NLTK data
#
# WHY DOCKER?
#   - "Works on my machine" → "Works everywhere"
#   - Isolation: Dependencies don't conflict with system
#   - Reproducibility: Same image = same behavior
#   - Deployment: Same image for dev, testing, production
#   - Scaling: Easy to run multiple containers
#
# DOCKER TERMINOLOGY:
#   - Image: Blueprint (like a class in OOP)
#   - Container: Running instance of image (like an object)
#   - Layer: Each command creates a layer (caching system)
#   - Registry: Repository for images (Docker Hub, AWS ECR)
#
# ==============================================================================

# BASE IMAGE: Start from official Python image
# ==============================================================================
# Format: FROM <image>:<tag>
#
# python:3.10-slim:
#   - python: Language runtime
#   - 3.10: Version (pinned for reproducibility)
#   - slim: Lightweight variant (no GUI, build tools)
#           vs 'latest' (includes extra stuff)
#
# WHY SLIM?
#   ✓ Smaller image (~150MB vs ~900MB)
#   ✓ Faster builds and deploys
#   ✓ Fewer security vulnerabilities (less software)
#   ✗ Need to manually install build tools if needed
#
# ALTERNATIVES:
#   - python:3.10 (default, includes build tools)
#   - python:3.10-alpine (even smaller, ~40MB, fewer packages)
#   - Ubuntu/Debian (custom runtime, more control)
#
FROM python:3.10-slim

# WORKING DIRECTORY: Set app folder inside container
# ==============================================================================
# WORKDIR /app
#
# What it does:
#   - Creates /app directory in container
#   - Sets current working directory (like cd /app)
#   - All subsequent commands run from here
#
# Best practice: Always set WORKDIR (don't assume /)
#
WORKDIR /app

# INSTALL SYSTEM DEPENDENCIES
# ==============================================================================
# apt-get update: Update package lists (like apt update)
# apt-get install: Install system packages (gcc needed for numpy compilation)
#
# gcc: GNU Compiler Collection
#   Needed for: Scientific libraries (numpy, scipy) need compilation
#   Trade-off: Larger image but allows compilation
#
# rm /var/lib/apt/lists/*: Delete package cache to reduce image size
#   Saves ~100MB (lists not needed after install, only in build)
#   Docker best practice: Clean up after apt commands
#
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# COPY APPLICATION FILES
# ==============================================================================
# COPY <from_host> <to_container>
#
# COPY backend/requirements.txt .
#   - Source: backend/requirements.txt (on your computer)
#   - Dest: . (current container dir = /app/)
#   - Result: /app/requirements.txt in container
#
# Why copy requirements first?
#   - Docker layers cache: If code changes, pip install doesn't re-run
#   - If code first: Any code change re-runs pip (slow, defeats caching)
#   - Solution: Copy stable requirements first, volatile code later
#
COPY backend/requirements.txt .

# INSTALL PYTHON DEPENDENCIES
# ==============================================================================
# pip install: Install packages from requirements.txt
#
# --no-cache-dir: Don't save pip cache in image
#   Saves ~100MB (cache not needed after install)
#   Docker best practice: Clean up build artifacts
#
RUN pip install --no-cache-dir -r requirements.txt

# DOWNLOAD NLTK DATA
# ==============================================================================
# NLTK packages (punkt tokenizer) need to be downloaded at build time
# Alternative: Download at runtime (slower startup)
# Best: Download at build time (baked into image)
#
# punkt: English tokenizer for sentence/word splitting
# Required by: train_and_save_model.py
#
RUN python -m nltk.downloader punkt

# COPY APPLICATION CODE
# ==============================================================================
# After dependencies are installed, copy application code
# Reason: Code changes often, dependencies change rarely
# Benefit: Faster rebuilds (cache pip install layer)
#
COPY backend/ .
COPY models/ ../models/

# EXPOSE PORT (metadata, doesn't actually publish)
# ==============================================================================
# EXPOSE 5000
#
# What it does: Document that app listens on port 5000
# Important: This is just information for developers/docs
#            Doesn't actually expose the port
#            Use: docker run -p 8000:5000 to map ports
#
EXPOSE 5000

# HEALTHCHECK (DevOps best practice)
# ==============================================================================
# Tells Docker/Kubernetes how to check if app is still healthy
# Used for: Auto-restart unhealthy containers
#
# Format: HEALTHCHECK [OPTIONS] CMD <command>
#
# --interval=30s: Check every 30 seconds
# --timeout=10s: Consider check failed if takes > 10 seconds
# --start-period=5s: Wait 5 seconds before checking (app startup time)
# --retries=3: Mark unhealthy after 3 failures
#
# CMD: Command to run health check
#   python -c "import requests; requests.get('http://localhost:5000/health')"
#   Calls the /health endpoint we defined in app.py
#
# Real-world use:
#   - Kubernetes restarts unhealthy pods
#   - Docker Compose can replace unhealthy containers
#   - Load balancers remove unhealthy instances
#
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# STARTUP COMMAND
# ==============================================================================
# CMD ["python", "app.py"]
#
# What it does: Default command when container starts
# Can be overridden: docker run <image> python train_and_save_model.py
#
# Format: CMD ["executable", "param1", "param2"]  (JSON array format)
#         CMD executable param1 param2            (shell format)
# Prefer JSON array (more predictable)
#
CMD ["python", "app.py"]

# ==============================================================================
# DOCKER BUILD EXAMPLE
# ==============================================================================
#
# Build image:
#   docker build -t movie-rec-api:1.0 -f backend/Dockerfile .
#
#   -t movie-rec-api:1.0  : Tag image with name and version
#   -f backend/Dockerfile : Path to this Dockerfile
#   .                      : Build context (current directory)
#
# Run container:
#   docker run -p 5000:5000 movie-rec-api:1.0
#
#   -p 5000:5000: Map port 5000 (container) to 5000 (host)
#
# See logs:
#   docker logs <container_id>
#
# Stop container:
#   docker stop <container_id>
#
# ==============================================================================
# MULTI-STAGE BUILDS (Advanced)
# ==============================================================================
#
# For ML apps, image can get large (numpy, scipy, scikit-learn = 500MB+)
# Multi-stage: Build in large image, copy only essentials to small image
#
# Example:
#   FROM python:3.10-slim as builder
#   ... build phase ...
#   
#   FROM python:3.10-slim
#   COPY --from=builder /app .
#   ... runtime phase ...
#
# Saves 30-50% image size (removes build tools after compilation)
#
# ==============================================================================
# LAYER CACHING STRATEGY
# ==============================================================================
#
# Docker builds layers and caches them:
#   Layer 1 (FROM): Download base image
#   Layer 2 (RUN apt-get): Install system deps
#   Layer 3 (COPY requirements): Copy requirements.txt
#   Layer 4 (RUN pip install): Install Python packages
#   Layer 5 (COPY code): Copy application code
#   Layer 6 (CMD): Set startup command
#
# Cache behavior:
#   ✓ If line unchanged: Use cached layer (instant)
#   ✗ If line changed: Rebuild from this layer onward (slow)
#
# Optimization: Order by change frequency
#   Least frequent (base image, system deps) → Most frequent (code)
#
# ==============================================================================
