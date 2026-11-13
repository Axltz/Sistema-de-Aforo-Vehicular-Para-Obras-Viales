import argparse
import sys

import cv2
import numpy as np

from src.config import DEFAULT_VIDEO_PATH, FRAME_SKIP_FACTOR, LIVE_FRAME_PATH
from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.analytics.processing import create_system_state, count_vehicles, calibrate_system
from src.storage.json_writer import save_metrics_local
from src.visualization.overlay import draw_overlay

# 1. PARSE CONSOLE ARGUMENTS
parser = argparse.ArgumentParser(description="Intelligent Vehicle Counting System for Roadworks")
parser.add_argument("--webcam", action="store_true", help="Use the webcam in real time instead of a video file")
parser.add_argument("--video", type=str, default=DEFAULT_VIDEO_PATH, help="Path to the video file to process")
args = parser.parse_args()

# Select the source
if args.webcam:
    video_source = 0
    print("🎥 SOURCE CONFIGURED: Real-time webcam (Channel 0)")
else:
    video_source = args.video
    print(f"🎬 SOURCE CONFIGURED: Video file '{video_source}'")

# 2. LOAD THE VIDEO / CAMERA
cap = cv2.VideoCapture(video_source)
if not cap.isOpened():
    print(f"❌ Error: Could not open the video source: {video_source}")
    sys.exit(1)

# 3. INITIALIZE TRACKING MEMORY
state = create_system_state()

frame_count = 0
result = None  # We will store the smart traffic diagnosis here

# MAIN LOOP: Read and process frames sequentially
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        if args.webcam:
            print("⚠️ Webcam connection lost.")
            break
        else:
            # If the video ends, restart it (infinite demo loop)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

    # Resize the frame to optimize display and speed
    h_orig, w_orig = frame.shape[:2]
    aspect = h_orig / w_orig
    frame = cv2.resize(frame, (1024, int(1024 * aspect)))

    frame_count += 1

    # ==========================================================================
    # STEP A: CALIBRATION CONDITIONAL WITH FRAME SKIPPING
    # ==========================================================================
    if not state["calibration_locked"]:
        # Run YOLO only on selected frames to save resources
        if frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in state:
            raw_detections = frame_detection(frame)

            # Filter by initial flow direction
            detected_vehicles = []
            for v in raw_detections:
                vid, curr = v["id"], np.array(v["center"])
                prev = np.array(state["ids_history"].get(vid, curr))

                if state["orientation"] == "vertical":
                    mov = (curr[1] - prev[1]) * state["flow_direction"]
                else:
                    mov = (curr[0] - prev[0]) * state["flow_direction"]

                if mov >= 0:
                    detected_vehicles.append(v)
            state["last_detections"] = detected_vehicles
            # Only save the frame when YOLO ran and there is something new to show
            cv2.imwrite(str(LIVE_FRAME_PATH), frame)
        else:
            # If we skip the frame, inherit the previous detections
            detected_vehicles = state["last_detections"]

        calibrate_system(detected_vehicles, frame.shape, state)
        cv2.putText(frame, f"CALIBRATING FLOW... {state['calibration_frames']}/30", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Traffic System - Main View", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # ==========================================================================
    # SYSTEM ALREADY CALIBRATED: OPTIMIZED PROCESSING WITH CROP AND YOLO SKIPPING
    # ==========================================================================
    # STEP B: FRAME CROP (drastically reduces the area YOLO processes)
    roi = state["active_roi"]
    cropped_frame = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]

    # STEP C: DETECTION WITH FRAME SKIPPING
    yolo_ran_this_frame = (frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in state)
    if yolo_ran_this_frame:
        raw_detections = frame_detection(cropped_frame)

        # Filter by travel direction
        detected_vehicles = []
        for v in raw_detections:
            vid, curr = v["id"], np.array(v["center"])
            prev = np.array(state["ids_history"].get(vid, curr))

            if state["orientation"] == "vertical":
                mov = (curr[1] - prev[1]) * state["flow_direction"]
            else:
                mov = (curr[0] - prev[0]) * state["flow_direction"]

            if mov >= 0:
                detected_vehicles.append(v)
        state["last_detections"] = detected_vehicles
    else:
        # Inherit the previous vehicle positions on the skipped frame
        detected_vehicles = state["last_detections"]

    # STEP D: VEHICLE COUNTER
    total_count, line = count_vehicles(detected_vehicles, state)

    # STEP E: TRAFFIC INTELLIGENCE (computed every 10 frames)
    if frame_count % 10 == 0 or result is None:
        result = process_frame(detected_vehicles, cropped_frame.shape, state)
        result["metrics"]["total_count"] = total_count

        # SAVE LOCALLY: write live.json every 10 frames and accumulate jsonl every 150
        append_log = (frame_count % 150 == 0)
        save_metrics_local(result["metrics"], append_to_log=append_log)

    # STEP F: DRAW THE VISUAL LAYERS (OVERLAYS)
    frame_with_overlay, dashboard = draw_overlay(cropped_frame, detected_vehicles, result)

    # Initialize the window sizes
    if frame_count == 1:
        cv2.namedWindow("Traffic System - Main View", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Traffic System - Main View", 800, int(800 * aspect))
        cv2.namedWindow("Control Dashboard", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Control Dashboard", 300, 500)

    # Render on screen
    cv2.imshow("Traffic System - Main View", frame_with_overlay)
    cv2.imshow("Control Dashboard", dashboard)
    # Only save when YOLO ran: the frame changed visually
    if yolo_ran_this_frame:
        cv2.imwrite(str(LIVE_FRAME_PATH), frame_with_overlay)

    # STEP G: CONTROL KEYBOARD
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break  # Shut down the system
    elif key == ord('e') or key == ord('E'):
        # Manual export of a Huffman-compressed report by pressing 'E'
        if result is not None:
            from src.analytics.processing import export_summary_json_huffman
            export_summary_json_huffman(result["metrics"])

cap.release()
cv2.destroyAllWindows()
print("👋 System shut down successfully.")
