import cv2
import json
from ultralytics import YOLO

from src.analytics.zonas import asignar_zona

# CARGAR MODELO YOLO
model = YOLO("yolov8n.pt")

# CARGAR VIDEO
video = cv2.VideoCapture("trafico.mp4")

dataset = {}

frame_num = 0
MAX_FRAMES = 40

# clases válidas
vehiculos_validos = ["car", "truck", "bus", "motorcycle"]

while True:

    ret, frame = video.read()

    if not ret:
        break

    resultados = model(frame)

    vehiculos_frame = []

    conteo_zonas = {
        "zona_1": 0,
        "zona_2": 0,
        "zona_3": 0
    }

    for r in resultados:

        for box in r.boxes:

            clase_id = int(box.cls[0])

            clase = model.names[clase_id]

            # filtrar solo vehículos
            if clase in vehiculos_validos:

                x1, y1, x2, y2 = box.xyxy[0]

                # calcular centro
                x = int((x1 + x2) / 2)
                y = int((y1 + y2) / 2)

                zona = asignar_zona(x, y)

                conteo_zonas[zona] += 1

                vehiculo = {

                    "tipo": clase,
                    "x": x,
                    "y": y,
                    "zona": zona
                }

                vehiculos_frame.append(vehiculo)

    total = len(vehiculos_frame)

    # estado del tráfico
    if total <= 3:
        estado = "fluido"

    elif total <= 6:
        estado = "medio"

    else:
        estado = "congestionado"

    dataset[f"frame_{frame_num}"] = {

        "vehiculos": vehiculos_frame,

        "total_vehiculos": total,

        "conteo_zonas": conteo_zonas,

        "densidad": "media",

        "clusters": 2,

        "estado": estado
    }

    frame_num += 1
    
    if frame_num >= MAX_FRAMES:
        break

# GUARDAR JSON
with open("dataset_trafico_real.json", "w") as archivo:

    json.dump(dataset, archivo, indent=4)

video.release()

print("Dataset JSON generado correctamente")