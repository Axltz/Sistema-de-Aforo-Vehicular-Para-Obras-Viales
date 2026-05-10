from ultralytics import YOLO
import numpy as np
import cv2

model = YOLO("yolo26n.pt")


def frame_detection(video_frame): 
    results = model.track(
        video_frame, 
        persist=True,
        classes=[2,3,5,7],
        verbose=False,
        conf=0.10,
        iou=0.3,
        imgsz=1024
    )



        
    boxes = results[0].boxes
    
    if boxes.id is None:
        return []
    
    detections = []

    ids = boxes.id.cpu().numpy().astype(int)
    coords = boxes.xyxy.cpu().numpy()

    for id_obj, box in zip(ids, coords):
       
        x1, y1, x2, y2 = box
        
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        detections.append(
        {
            "id": id_obj,
            "bbox": (int(x1), int(y1), int(x2), int(y2)),
            "center": (cx, cy)
        }    
        )

    return detections
