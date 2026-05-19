# ==============================================================================
# detection.py - MÓDULO DE DETECCIÓN Y RASTREO CON IA (YOLO)
# ==============================================================================
# Este módulo inicializa la red neuronal YOLOv8/YOLOv11 de Ultralytics
# y se encarga de analizar los frames de video para localizar y rastrear (track)
# vehículos individualmente mediante algoritmos internos de tracking (ByteTrack/BoT-SORT).

from ultralytics import YOLO
import numpy as np
import cv2

# Inicializamos el modelo nano de YOLO preentrenado (pesos ligeros y rápidos)
# Nota: La primera vez que se corra, descargará automáticamente "yolo26n.pt" o similar de internet.
model = YOLO("yolo26n.pt")


def frame_detection(video_frame): 
    """
    Recibe un frame de video y ejecuta la detección/rastreo de vehículos.
    Retorna una lista limpia de diccionarios con ID, BBox (caja delimitadora) y Centroide.
    """
    # Ejecutamos el rastreo con YOLO en el frame
    results = model.track(
        video_frame, 
        persist=True,               
        classes=[1, 2, 3, 5, 6, 7], # Filtramos clases de COCO Dataset: 1:Bici, 2:Carro, 3:Moto, 5:Bus, 6:Tren, 7:Camión
        verbose=False,              # Desactivamos los prints excesivos en consola para no ensuciarla
        conf=0.005,                 
        iou=0.45,                 
        imgsz=800                   # Redimensionado interno de imagen para optimizar precisión en YOLO
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

        detections.append({
            "id": id_obj,
            "bbox": (int(x1), int(y1), int(x2), int(y2)),
            "center": (cx, cy)
        })

    return detections
