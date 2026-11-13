#!/usr/bin/env bash
# Roadwork Vehicle Traffic Monitoring System - portable launcher.
#
# Usage:
#   ./run.sh          -> live CLI (opens windows)
#   ./run.sh gui      -> desktop GUI
#   ./run.sh demo     -> annotated demo video, no windows
#   ./run.sh test     -> unit tests
set -e
cd "$(dirname "$0")"

if command -v python3.11 >/dev/null 2>&1; then
  PY=python3.11
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "[ERROR] Python was not found. Install Python 3.11 or newer."
  exit 1
fi

echo "============================================================"
echo "  Roadwork Vehicle Traffic Monitoring System"
echo "============================================================"

if [ -x "venv/bin/python" ]; then
  VENV_DIR=venv
else
  VENV_DIR=.venv
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "[1/3] Creating the Python environment in .venv ..."
  "$PY" -m venv .venv
  VENV_DIR=.venv
fi

VENV_PY="$VENV_DIR/bin/python"

if [ ! -f "$VENV_DIR/.deps-installed" ]; then
  echo "[2/3] Installing dependencies. The first run can take several minutes..."
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install -r requirements-portable.txt
  touch "$VENV_DIR/.deps-installed"
fi

echo "[3/3] Starting..."
echo

case "${1:-}" in
  demo)
    shift
    exec "$VENV_PY" -m scripts.demo "$@"
    ;;
  gui)
    exec "$VENV_PY" -m src.app
    ;;
  test)
    "$VENV_PY" -m pytest --version >/dev/null 2>&1 || "$VENV_PY" -m pip install -q pytest
    exec "$VENV_PY" -m pytest -q
    ;;
  *)
    exec "$VENV_PY" -m src.main "$@"
    ;;
esac
