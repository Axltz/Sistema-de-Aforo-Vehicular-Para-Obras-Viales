from pathlib import Path

# Directorios base del proyecto
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"

# Rutas de almacenamiento local
METRICS_LIVE_PATH = DATA_DIR / "metrics_live.json"

# Configuración del video y procesamiento
DEFAULT_VIDEO_PATH = "data/videos/trafico3.mp4"
FRAME_SKIP_FACTOR = 3  # Procesar YOLO cada N frames para optimizar CPU/GPU
