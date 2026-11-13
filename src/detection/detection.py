# ==============================================================================
# detection.py - AI DETECTION AND TRACKING MODULE (YOLO)
# ==============================================================================
# This module initializes the Ultralytics YOLO neural network and analyzes video
# frames to locate and track individual vehicles using built-in tracking
# algorithms (ByteTrack / BoT-SORT).

from ultralytics import YOLO

from src.config import YOLO_MODEL_PATH

# Initialize the pre-trained YOLO nano model (lightweight, fast weights).
# Note: On the first run it will automatically download "yolo26n.pt" (or
# similar) if the file is not present locally.
model = YOLO(YOLO_MODEL_PATH)


def frame_detection(video_frame):
    """
    Receives a video frame and runs vehicle detection/tracking.
    Returns a clean list of dictionaries with ID, bounding box and centroid.
    """
    # Run YOLO tracking on the frame
    results = model.track(
        video_frame,
        persist=True,
        # COCO classes: 1:bicycle, 2:car, 3:motorcycle, 5:bus, 6:train, 7:truck
        classes=[1, 2, 3, 5, 6, 7],
        verbose=False,  # Disable excessive console output
        conf=0.005,
        iou=0.45,
        imgsz=800,  # Internal image resize to optimize YOLO precision
    )

    boxes = results[0].boxes

    if boxes.id is None:
        return []

    detections = []

    ids = boxes.id.cpu().numpy().astype(int)
    coords = boxes.xyxy.cpu().numpy()

    for object_id, box in zip(ids, coords):
        x1, y1, x2, y2 = box

        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        detections.append({
            "id": object_id,
            "bbox": (int(x1), int(y1), int(x2), int(y2)),
            "center": (cx, cy)
        })

    return detections
