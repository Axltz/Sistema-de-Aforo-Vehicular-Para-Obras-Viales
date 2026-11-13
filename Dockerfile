# ==============================================================================
# Dockerfile - Intelligent Vehicle Counting System for Roadworks
# ------------------------------------------------------------------------------
# Lightweight Linux image (Debian "slim") with Python 3.11, ready to run the
# OpenCV + YOLO/Ultralytics pipeline.
#
# Build:  docker build -t vehicle-counter .
# Run:    docker run --rm vehicle-counter python -m src.main --help
# ==============================================================================

# 1) BASE IMAGE
#    Official Python 3.11 on Debian "slim": small footprint, no build extras.
FROM python:3.11-slim

# 2) PYTHON RUNTIME FLAGS
#    - PYTHONDONTWRITEBYTECODE: do not generate .pyc files inside the image.
#    - PYTHONUNBUFFERED:        flush stdout/stderr immediately (visible logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) WORKING DIRECTORY
#    All following instructions run inside /app.
WORKDIR /app

# 4) SYSTEM LIBRARIES (required by OpenCV and PyTorch/YOLO at runtime)
#    - libgl1                       : OpenGL loader used by OpenCV (cv2).
#    - libglib2.0-0                 : GLib runtime used by OpenCV/GTK.
#    - libgomp1                     : OpenMP runtime required by PyTorch.
#    - libsm6 / libxext6 / libxrender1 : X11 libraries used by OpenCV highgui.
#    The apt cache is removed afterwards to keep the image small.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# 5) DEPENDENCIES (copied first to leverage Docker layer caching)
#    If only the source code changes, this layer is reused and pip does not
#    reinstall everything.
COPY requirements.txt .

# 6) INSTALL PYTHON PACKAGES
#    Upgrade pip and install the pinned dependencies without keeping the cache.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7) APPLICATION SOURCE
#    Copy the rest of the project (filtered by .dockerignore).
COPY . .

# 8) DEFAULT COMMAND
#    Launch the OpenCV pipeline entry point. OpenCV opens GUI windows, so a
#    display (X11) is required to *see* it; for a headless check use:
#    docker run --rm vehicle-counter python -m src.main --help
CMD ["python", "-m", "src.main"]
