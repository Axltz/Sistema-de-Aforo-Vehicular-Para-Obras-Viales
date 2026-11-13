"""Build a small image gallery from a generated demo video.

Extracts stills (calibration, detection, final dashboard) and an animated GIF
preview. No windows are opened.

Usage:
    python -m scripts.gallery
    python -m scripts.gallery --video demo/demo_trafico2.mp4 --outdir demo/images
"""

import argparse
from pathlib import Path

import cv2
from PIL import Image

from src.config import BASE_DIR


def _read_frame(cap, index):
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = cap.read()
    return frame if ok else None


def _right_panel(frame):
    """Crop the analytics panel (400x700 at native size) from a composed frame."""
    height, width = frame.shape[:2]
    panel_width = round(400 * height / 700)
    return frame[:, max(0, width - panel_width):]


def build_gallery(video_path, outdir, calibration_frame=10, gif_seconds=4,
                  gif_fps=8, gif_width=480):
    video_path = Path(video_path)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open the demo video: {video_path}")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0

    middle = max(1, total * 55 // 100)
    last = max(1, total - 2)

    stills = {
        "01_calibration.png": calibration_frame,
        "02_detections.png": middle,
        "03_final_dashboard.png": last,
    }

    written = []
    for name, index in stills.items():
        frame = _read_frame(cap, index)
        if frame is None:
            continue
        path = outdir / name
        cv2.imwrite(str(path), frame)
        written.append(path)

    final_frame = _read_frame(cap, last)
    if final_frame is not None:
        path = outdir / "04_dashboard_panel.png"
        cv2.imwrite(str(path), _right_panel(final_frame))
        written.append(path)

    # Animated GIF preview
    gif_path = outdir / "preview.gif"
    step = max(1, round(fps / gif_fps))
    limit = min(total, int(gif_seconds * fps))
    frames = []
    for index in range(0, limit, step):
        frame = _read_frame(cap, index)
        if frame is None:
            break
        height, width = frame.shape[:2]
        new_height = round(height * gif_width / width)
        frame = cv2.resize(frame, (gif_width, new_height))
        frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))

    cap.release()

    if frames:
        frames[0].save(
            str(gif_path),
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / gif_fps),
            loop=0,
            optimize=True,
        )
        written.append(gif_path)

    for path in written:
        print(f"  {path.relative_to(BASE_DIR)}  "
              f"({path.stat().st_size / 1024:.0f} KB)")

    return written


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Extract stills and a GIF from a generated demo video."
    )
    parser.add_argument(
        "--video",
        default="demo/demo_trafico1.mp4",
        help="Demo video (default: %(default)s)",
    )
    parser.add_argument(
        "--outdir",
        default="demo/images",
        help="Output folder (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    video = Path(args.video)
    if not video.is_absolute():
        video = BASE_DIR / video

    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = BASE_DIR / outdir

    build_gallery(video, outdir)


if __name__ == "__main__":
    main()
