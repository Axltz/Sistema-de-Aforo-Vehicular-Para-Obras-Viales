# Architecture

This document explains the real technical decisions behind the Roadwork Vehicle
Traffic Monitoring System: the modular layout under `src/`, the use of DBSCAN
for congestion detection, the in-house Huffman codec for low-bandwidth
telemetry, and environment-based configuration.

---

## 1. Pipeline Overview

Every processed frame follows the same sequence, shared by the GUI and the CLI:

```
capture frame -> resize to width 1024
  -> if not calibrated: detect on full frame, calibrate, render "CALIBRATING FLOW"
  -> else: crop ROI, detect on cropped ROI, filter by flow direction
           count line crossings
           every 10 frames: build graph + DBSCAN + metrics
           draw overlay
```

`src/pipeline/pipeline.py` orchestrates the per-frame analytics and returns a
result object with `metrics`, `clusters`, `graph` and `line`.

---

## 2. Modular Separation in `src/`

The code is split by responsibility so that the computer-vision, analytics,
storage and presentation layers can evolve independently:

| Package / module | Responsibility |
|---|---|
| `src/config.py` | Environment-driven configuration and path resolution |
| `src/detection/` | The only place that loads and runs the YOLO model |
| `src/pipeline/` | Per-frame orchestration of graph, clustering and metrics |
| `src/analytics/graphs.py` | Proximity graph over vehicle centroids |
| `src/analytics/clustering.py` | DBSCAN clustering of vehicle positions |
| `src/analytics/metrics.py` | Flow, density, state, trend and risk metrics |
| `src/analytics/processing.py` | State, calibration, counting and Huffman export |
| `src/analytics/huffman.py` | Huffman compress/decompress |
| `src/storage/json_writer.py` | Live snapshot, JSONL history and JSON export |
| `src/visualization/overlay.py` | Video annotation and dashboard rendering |
| `src/gui.py`, `src/main.py`, `src/app.py` | Presentation and entry points |

Consequences of this split:

- **One inference site.** `src/detection/detection.py` centralizes the model
  and inference parameters (confidence, IoU, image size, class filter), so the
  calibration and normal-operation paths cannot drift apart.
- **Analytics are pure functions.** Graph, clustering and metric functions
  receive data and return data; they do not read files or open windows. This is
  what makes them unit-testable without YOLO or a display.
- **Two UIs, one core.** The GUI and CLI both call the same `process_frame`
  pipeline, so behavior stays consistent.

---

## 3. DBSCAN for Congestion Detection

After calibration, vehicles are represented by their centroids. Two spatial
structures are built:

- **Proximity graph** (`src/analytics/graphs.py`): an undirected edge is added
  between two vehicles when their Euclidean distance is below
  `distance_factor * frame_width` (default `0.05`, i.e. 5% of the width).
- **DBSCAN** (`src/analytics/clustering.py`) with `eps = 0.10 * frame_width`
  (10% of the width) and `min_samples = 3`.

Why DBSCAN:

- The number of clusters does not need to be known in advance, which suits
  traffic scenes of varying density.
- Points in low-density regions are labeled as noise (`-1`) and discarded, so
  isolated vehicles do not create false congestion groups.
- A group only exists when at least three vehicles are mutually close, matching
  the intent of "vehicles bunched together".

Each resulting cluster is classified in `calculate_metrics`:

- **High risk** when flow `< 3` and the group has `>= 4` vehicles (raises
  `congestion_alert`).
- **Medium risk** when the group has `>= 3` vehicles and flow `< 10`.
- **Low risk** otherwise.

The cluster count and graph edge count also feed the spatial interaction
percentage, which combines grouping ratio and connection density.

---

## 4. Huffman Compression for Low-Bandwidth Telemetry

`src/analytics/huffman.py` implements the codec from scratch:

1. Count character frequencies with `collections.Counter`.
2. Build the tree with a min-heap (`heapq`) keyed by frequency.
3. Derive prefix codes by walking the tree (left = `0`, right = `1`).
4. Encode the JSON string into a bit string.
5. Pack bits into bytes in 8-bit chunks, padding the final chunk with `0`.
6. Write the `.bin` payload plus a `*_dict.json` sidecar holding the code table.

Decompression rebuilds the reversed table, decodes the bit string, and trims to
the last `}` of the JSON. That trim is deliberate: zero-padding used to fill the
final byte can otherwise decode into extra characters after the real document.

**Why this design:** the code table travels next to the payload, so the receiver
can decode without any external library or shared state. This keeps telemetry
self-contained and compact for constrained links, at the cost of sending the
dictionary each time.

---

## 5. Environment Variable Handling

`src/config.py` centralizes configuration:

- Paths are read from `DEFAULT_VIDEO_PATH`, `YOLO_MODEL_PATH` and
  `LIVE_FRAME_PATH`, each with a sensible default.
- `python-dotenv` loads a local `.env` file if present; the import is wrapped in
  `try/except` so the app still runs with real environment variables when the
  package is not installed.
- Relative paths are resolved against `BASE_DIR` (the project root), so the
  application behaves the same regardless of the current working directory.

Keeping configuration in one module avoids hard-coded paths scattered across the
code and makes the Docker and local workflows interchangeable.

---

## 6. Counting Semantics

`count_vehicles` uses the sign of the 2D cross product to detect which side of
the line a vehicle is on, and counts when the side changes between frames. Two
safeguards apply:

- vehicles moving opposite to the calibrated `flow_direction` are skipped;
- `counted_ids` prevents a vehicle from being counted twice.

As a result, counting is **directional**: calibration infers one dominant flow
direction per run, and only that direction is counted. The system does not count
both directions simultaneously.

---

## 7. Testing

The tests in `tests/` target pure functions only: the Huffman round trip, the
metrics schema, and the graph/clustering helpers. They avoid the YOLO model and
any GUI, so they run deterministically in CI without a display.

---

## 8. Portable Execution and Headless Demo

Two additions make the project usable without manual Python setup:

- **`run.bat` / `run.sh`** create a local `.venv` on first use, install
  `requirements-portable.txt` (unpinned versions) and dispatch to a mode:
  CLI, GUI, demo or tests. `requirements.txt` keeps the exact pins used by
  Docker and CI, so reproducibility is preserved where it matters.
- **`scripts/demo.py`** reuses the same functions as `src/main.py`
  (`frame_detection`, `calibrate_system`, `count_vehicles`, `process_frame`,
  `draw_overlay`) but writes frames to a `cv2.VideoWriter` instead of calling
  `cv2.imshow`. Because it never opens a window, it runs headless (SSH,
  containers, CI). The annotated ROI is pasted back into the full frame so the
  output keeps a constant resolution, and a JSON summary records the
  calibration result and final metrics.

The demo intentionally duplicates the frame loop instead of refactoring the
entry points into a shared loop function. Keeping the change additive avoided
risking the behavior of the GUI and CLI in the same step; extracting a shared
`process_stream()` would be the natural follow-up refactor.

---

## 9. Known Limitations

- Counting is directional, not simultaneous two-way counting.
- No performance or accuracy benchmarks are included.
- The Docker image targets the CLI; the GUI needs Tkinter and a display.
- Huffman decompression assumes the payload is a single JSON object.
