"""Headless demo generator.

Runs the real detection + analytics pipeline on a video and writes an
annotated MP4 plus a JSON summary. It opens no windows, so it works on any
machine (including a Docker container or a remote server).

Usage:
    python -m scripts.demo
    python -m scripts.demo --video data/videos/trafico2.mp4 --max-frames 450
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from src.analytics.processing import (
    calibrate_system,
    count_vehicles,
    create_system_state,
)
from src.config import BASE_DIR, DEFAULT_VIDEO_PATH
from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.visualization.overlay import draw_overlay

TARGET_WIDTH = 1024        # same resize used by src/main.py and src/gui.py
CALIBRATION_FRAMES = 30    # same threshold as calibrate_system
METRICS_EVERY = 10         # same cadence as src/main.py


def _filter_by_direction(detections, state):
    """Drop vehicles moving against the calibrated flow direction."""
    filtered = []
    for v in detections:
        vid, curr = v["id"], np.array(v["center"])
        prev = np.array(state["ids_history"].get(vid, curr))

        if state["orientation"] == "vertical":
            movement = (curr[1] - prev[1]) * state["flow_direction"]
        else:
            movement = (curr[0] - prev[0]) * state["flow_direction"]

        if movement >= 0:
            filtered.append(v)

    return filtered


def _json_default(value):
    """Convert NumPy scalar/array values so the summary is JSON serializable."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (set, tuple)):
        return list(value)
    return str(value)


def _compose_frame(main, dashboard):
    """Place the annotated video and the analytics dashboard side by side."""
    main_h, main_w = main.shape[:2]

    if dashboard is None:
        dashboard = np.full((700, 400, 3), 30, dtype=np.uint8)
        cv2.putText(
            dashboard, "WAITING FOR", (45, 330),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2,
        )
        cv2.putText(
            dashboard, "CALIBRATION", (45, 370),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2,
        )

    panel_h, panel_w = dashboard.shape[:2]
    gap = 8
    canvas_h = max(main_h, panel_h)

    canvas = np.full((canvas_h, main_w + gap + panel_w, 3), 18, dtype=np.uint8)
    y_main = (canvas_h - main_h) // 2
    canvas[y_main:y_main + main_h, 0:main_w] = main
    canvas[0:panel_h, main_w + gap:main_w + gap + panel_w] = dashboard
    cv2.line(canvas, (main_w + gap // 2, 0),
             (main_w + gap // 2, canvas_h), (70, 70, 70), 1)

    return canvas


def _open_writer(path, frame_size, fps):
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, frame_size)
    if not writer.isOpened():
        raise RuntimeError(
            "OpenCV could not create the output video. "
            "Try a different --output name or install a build with MP4 support."
        )
    return writer


def generate_demo(video_path, output_path, max_frames=None, scale=1.0,
                  show_dashboard=True):
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open the video source: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if fps <= 0:
        fps = 30.0

    state = create_system_state()
    writer = None
    frame_count = 0
    last_result = None
    last_dashboard = None
    calibration_locked = False

    print(f"Source : {video_path}")
    print(f"Output : {output_path}")
    print("Processing frames (no window will open)...")

    while True:
        if max_frames is not None and frame_count >= max_frames:
            break

        ret, frame = cap.read()
        if not ret:
            break

        # Same resize as the real entry points.
        height, width = frame.shape[:2]
        aspect = height / width
        frame = cv2.resize(frame, (TARGET_WIDTH, int(TARGET_WIDTH * aspect)))
        frame_count += 1

        if not state["calibration_locked"]:
            raw = frame_detection(frame)
            detections = _filter_by_direction(raw, state)
            state["last_detections"] = detections

            calibrate_system(detections, frame.shape, state)

            cv2.putText(
                frame,
                f"CALIBRATING FLOW... {state['calibration_frames']}/{CALIBRATION_FRAMES}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2,
            )
            output_frame = frame
        else:
            calibration_locked = True
            roi = state["active_roi"]
            cropped = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]

            raw = frame_detection(cropped)
            detections = _filter_by_direction(raw, state)

            total_count, _ = count_vehicles(detections, state)

            if frame_count % METRICS_EVERY == 0 or last_result is None:
                last_result = process_frame(detections, cropped.shape, state)
                last_result["metrics"]["total_count"] = total_count

            annotated, dashboard = draw_overlay(
                cropped.copy(), detections, last_result
            )
            last_dashboard = dashboard

            # Paste the annotated ROI back into the full frame so the output
            # video keeps a constant resolution during the whole clip.
            output_frame = frame.copy()
            output_frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]] = annotated

        if show_dashboard:
            output_frame = _compose_frame(output_frame, last_dashboard)

        if scale != 1.0:
            new_size = (
                int(output_frame.shape[1] * scale),
                int(output_frame.shape[0] * scale),
            )
            output_frame = cv2.resize(output_frame, new_size)

        if writer is None:
            writer = _open_writer(
                output_path,
                (output_frame.shape[1], output_frame.shape[0]),
                fps,
            )

        writer.write(output_frame)

        if frame_count % 25 == 0:
            print(f"  {frame_count} frames processed...", end="\r", flush=True)

    cap.release()
    if writer is not None:
        writer.release()

    if last_dashboard is not None:
        dashboard_path = output_path.parent / "dashboard.png"
        cv2.imwrite(str(dashboard_path), last_dashboard)
    else:
        dashboard_path = None

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_video": str(video_path),
        "output_video": str(output_path),
        "frames_processed": frame_count,
        "video_fps": round(float(fps), 2),
        "video_seconds": round(frame_count / fps, 1) if fps else None,
        "calibration_locked": calibration_locked,
        "calibration": {
            "orientation": state["orientation"],
            "flow_direction": state["flow_direction"],
            "roi": state.get("active_roi"),
            "line": {
                "start": list(state["line"]["start"]),
                "end": list(state["line"]["end"]),
            },
        },
        "total_count": state["total_count"],
        "final_metrics": last_result["metrics"] if last_result else None,
        "dashboard_image": str(dashboard_path) if dashboard_path else None,
    }

    summary_path = output_path.parent / "demo_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=_json_default)

    print()
    print("=" * 60)
    print(" DEMO GENERATED")
    print("=" * 60)
    print(f" Video      : {output_path}")
    print(f" Summary    : {summary_path}")
    if dashboard_path:
        print(f" Dashboard  : {dashboard_path}")
    print(f" Frames     : {frame_count}")
    print(f" Calibrated : {calibration_locked} "
          f"(orientation={state['orientation']}, direction={state['flow_direction']})")
    print(f" Crossings  : {state['total_count']}")
    if last_result:
        metrics = last_result["metrics"]
        print(f" Final state: {metrics['flow_state']} | "
              f"{metrics['flow_per_minute']} veh/min | "
              f"{metrics['total_vehicles']} in scene")
    print("=" * 60)

    if not calibration_locked:
        print(" WARNING: calibration never locked (not enough moving vehicles).")

    return summary


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate an annotated demo video (headless, no windows)."
    )
    parser.add_argument(
        "--video",
        default=DEFAULT_VIDEO_PATH,
        help="Input video file (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output MP4 path (default: demo/demo_<video_name>.mp4)",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=450,
        help="Stop after N frames; 0 means process the whole video (default: 450)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Output scale factor, e.g. 0.75 for a smaller file (default: 1.0)",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Only render the annotated video, without the analytics panel",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    video = Path(args.video)
    if not video.is_absolute():
        video = BASE_DIR / video

    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = BASE_DIR / output
    else:
        output = BASE_DIR / "demo" / f"demo_{video.stem}.mp4"

    max_frames = None if args.max_frames in (0, None) else args.max_frames

    generate_demo(
        video,
        output,
        max_frames=max_frames,
        scale=args.scale,
        show_dashboard=not args.no_dashboard,
    )


if __name__ == "__main__":
    main()
