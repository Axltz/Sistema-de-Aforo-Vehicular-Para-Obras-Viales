import os
from pathlib import Path

# Project base directories
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"

# Load environment variables from the project root ".env" file (if present).
# Falls back to the real environment when python-dotenv is not installed.
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def _resolve_path(value):
    """Return a Path, resolving relative paths against the project root."""
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


# Local storage paths
METRICS_LIVE_PATH = DATA_DIR / "metrics_live.json"
LIVE_FRAME_PATH = _resolve_path(os.getenv("LIVE_FRAME_PATH", "data/live_frame.jpg"))

# Video and processing configuration
DEFAULT_VIDEO_PATH = str(_resolve_path(os.getenv("DEFAULT_VIDEO_PATH", "data/videos/trafico1.mp4")))
FRAME_SKIP_FACTOR = 1  # Run YOLO on every frame to avoid losing precision in the tracker.

# YOLO model weights (auto-downloaded on first run if missing)
YOLO_MODEL_PATH = str(_resolve_path(os.getenv("YOLO_MODEL_PATH", "models/yolo26n.pt")))
