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
        persist=True,               # persist=True mantiene los IDs constantes entre cuadros consecutivos
        classes=[1, 2, 3, 5, 6, 7], # Filtramos clases de COCO Dataset: 1:Bici, 2:Carro, 3:Moto, 5:Bus, 6:Tren, 7:Camión
        verbose=False,              # Desactivamos los prints excesivos en consola para no ensuciarla
        conf=0.005,                 # Umbral de confianza bajo para detectar autos incluso lejanos en vertical
        iou=0.45,                   # IoU (Intersection over Union) para supresión de no máximos (elimina duplicados)
        imgsz=800                   # Redimensionado interno de imagen para optimizar precisión en YOLO
    )

    # Extraemos las cajas delimitadoras (Bounding Boxes) del resultado
    boxes = results[0].boxes
    
    # Si YOLO no detecta absolutamente nada en este cuadro, retornamos lista vacía
    if boxes.id is None:
        return []
    
    detections = []

    # Extraemos los IDs de rastreo y las coordenadas absolutas de las cajas (BBoxes)
    ids = boxes.id.cpu().numpy().astype(int)
    coords = boxes.xyxy.cpu().numpy()

    # Iteramos cada objeto detectado para construir nuestro diccionario de datos
    for id_obj, box in zip(ids, coords):
        # Desempaquetamos coordenadas: x1/y1 (arriba-izquierda), x2/y2 (abajo-derecha)
        x1, y1, x2, y2 = box
        
        # Calculamos matemáticamente el Centroide del vehículo (centro físico de la caja)
        # Esto sirve para evaluar si el carro cruza la línea o se une a grupos.
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        detections.append({
            "id": id_obj,
            "bbox": (int(x1), int(y1), int(x2), int(y2)),
            "center": (cx, cy)
        })

    return detections
