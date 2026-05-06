import cv2
from ultralytics import YOLO
import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analytics.procesamiento import procesar_frame, clasificar_trafico, detectar_patron, comparar_frames

print("Cargando el Modelo YOLO con Tracking... (esto puede tomar unos segundos)")
model = YOLO('yolov8n.pt') 

video_path = 'src/detection/trafico.mp4' 
print(f"Intentando abrir el video: {video_path}")

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"No se encontro el video, Verifica que '{video_path}'")
else:
    print("Video encontrado. Iniciando detección y conteo... (Presiona 'q' para salir)")

ventana_frames = 30  
historial_vehiculos = []
anterior_analisis = None
contador_frames = 0
conteo_total = 0
ids_contados = set()

LINEA_Y = 400
ZONA_1_X = 285
ZONA_2_X = 570

while cap.isOpened():
    exito, frame = cap.read()
    
    if exito:
        contador_frames += 1
        resultados = model.track(frame, persist=True, classes=[2, 3, 5, 7], verbose=False, conf=0.45, iou=0.5)
        
        cajas = resultados[0].boxes
        centros_actuales = []
        
        if cajas.id is not None:
            ids = cajas.id.cpu().numpy().astype(int)
            coords = cajas.xyxy.cpu().numpy()
            
            for id_obj, box in zip(ids, coords):
                x1, y1, x2, y2 = box
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                centros_actuales.append((cx, cy))
                
                if cy > LINEA_Y and id_obj not in ids_contados:
                    conteo_total += 1
                    ids_contados.add(id_obj)
                
                cv2.putText(frame, f"ID: {id_obj}", (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

        historial_vehiculos.append(centros_actuales)
        if len(historial_vehiculos) > ventana_frames:
            historial_vehiculos.pop(0)

        analisis = procesar_frame(centros_actuales)
        promedio_v = sum(len(f) for f in historial_vehiculos) / len(historial_vehiculos)
        analisis["n_vehiculos"] = int(promedio_v)
        
        estado = clasificar_trafico(analisis["densidad"], analisis["dispersion"], analisis["n_clusters"])
        patron = detectar_patron(analisis["zonas"])
        cambio = comparar_frames(analisis, anterior_analisis)
        z = analisis["zonas"]
        labels = analisis["labels"]

        textos = [
            f"Vehiculos en frame: {len(centros_actuales)}",
            f"CONTEO TOTAL: {conteo_total}",
            f"Estado: {estado}",
            f"Densidad: {analisis['densidad']}",
            f"Clusters (Embotellamientos): {analisis['n_clusters']}",
            f"Dispersion: {analisis['dispersion']:.0f}"
        ]
        
        dashboard = np.zeros((300, 500, 3), dtype=np.uint8) 
        cv2.rectangle(dashboard, (0, 0), (500, 300), (40, 40, 40), -1) 
        cv2.putText(dashboard, "SISTEMA DE AFORO VIAL", (10, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2)
        cv2.line(dashboard, (10, 40), (480, 40), (255, 255, 255), 1)

        for i, line in enumerate(textos):
            y = 80 + i * 40
            cv2.putText(dashboard, f"> {line}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        frame_anotado = frame.copy()
        
        cv2.line(frame_anotado, (0, LINEA_Y), (frame.shape[1], LINEA_Y), (255, 255, 255), 2)
        cv2.putText(frame_anotado, f"CONTEO: {conteo_total}", (10, LINEA_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        for i, (cx, cy) in enumerate(centros_actuales):
            if i < len(labels):
                label = labels[i]
                if label != -1:
                    color = (255, 0, 255) 
                    cv2.circle(frame_anotado, (cx, cy), 5, color, -1)
                    for j in range(i + 1, len(centros_actuales)):
                        if j < len(labels) and labels[j] == label:
                            cx2, cy2 = centros_actuales[j]
                            cv2.line(frame_anotado, (cx, cy), (cx2, cy2), color, 1)

        cv2.imshow("Video - Deteccion y Conteo", frame_anotado)
        cv2.imshow("Dashboard - Metricas de Trafico", dashboard)

        if contador_frames % 15 == 0:
            print(f"Frame {contador_frames} | Conteo Total: {conteo_total} | Vehiculos en frame: {len(centros_actuales)}")
            anterior_analisis = analisis

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    else:
        print("Fin del video.")
        break

cap.release()
cv2.destroyAllWindows()


