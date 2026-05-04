import cv2
from ultralytics import YOLO
import sys
import os

# Añadir el directorio raíz al path para poder importar analytics
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analytics.procesamiento import procesar_frame, clasificar_trafico, detectar_patron, comparar_frames

print("Cargando el Modelo YOLO... (esto puede tomar unos segundos)")
model = YOLO('yolov8n.pt') 

video_path = 'src/detection/trafico.mp4' 
print(f"Intentando abrir el video: {video_path}")

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"No se encontro el video, Verifica que '{video_path}'")
else:
    print("Video encontrado. Iniciando detección... (Presiona 'q' en el video para salir)")

# --- CONFIGURACIÓN DE VENTANA DE ANÁLISIS ---
ventana_frames = 30  
historial_vehiculos = []
anterior_analisis = None
contador_frames = 0

while cap.isOpened():
    exito, frame = cap.read()
    
    if exito:
        contador_frames += 1
        # verbose=False para limpiar la consola
        resultados = model(frame, classes=[2, 3, 5, 7], verbose=False)
        
        cajas = resultados[0].boxes
        centros_actuales = []
        
        for caja in cajas:
            x1, y1, x2, y2 = caja.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
            centros_actuales.append((cx, cy))
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

        # Guardar en el historial para suavizado
        historial_vehiculos.append(centros_actuales)
        if len(historial_vehiculos) > ventana_frames:
            historial_vehiculos.pop(0)

        # 1. ANÁLISIS REAL
        analisis = procesar_frame(centros_actuales)
        promedio_v = sum(len(f) for f in historial_vehiculos) / len(historial_vehiculos)
        analisis["n_vehiculos"] = int(promedio_v)
        
        estado = clasificar_trafico(analisis["densidad"], analisis["dispersion"], analisis["n_clusters"])
        patron = detectar_patron(analisis["zonas"])
        cambio = comparar_frames(analisis, anterior_analisis)
        z = analisis["zonas"]
        labels = analisis["labels"]

        # 2. VISUALIZACIÓN EN VIDEO
        textos = [
            f"Vehiculos: {analisis['n_vehiculos']} | Densidad: {analisis['densidad']}",
            f"Estado: {estado}",
            f"Patron: {patron}",
            f"Cambio: {cambio}",
            f"Clusters: {analisis['n_clusters']} | Disp: {analisis['dispersion']:.0f}"
        ]
        
        # --- PANEL DE DASHBOARD ---
        import numpy as np
        dashboard = np.zeros((300, 500, 3), dtype=np.uint8) 
        cv2.rectangle(dashboard, (0, 0), (500, 300), (40, 40, 40), -1) 
        cv2.putText(dashboard, "DASHBOARD DE ANALISIS", (10, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2)
        cv2.line(dashboard, (10, 40), (480, 40), (255, 255, 255), 1)

        for i, line in enumerate(textos):
            y = 80 + i * 40
            cv2.putText(dashboard, f"> {line}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        frame_anotado = resultados[0].plot()
        
        # --- DIBUJAR GRAFO DE PROXIMIDAD EN EL VIDEO ---
        for i, (cx, cy) in enumerate(centros_actuales):
            label = labels[i]
            if label != -1:
                color = (255, 0, 255) # Rosa
                cv2.circle(frame_anotado, (cx, cy), 5, color, -1)
                for j in range(i + 1, len(centros_actuales)):
                    if labels[j] == label:
                        cx2, cy2 = centros_actuales[j]
                        cv2.line(frame_anotado, (cx, cy), (cx2, cy2), color, 1)

        cv2.imshow("Video - Deteccion YOLO", frame_anotado)
        cv2.imshow("Dashboard - Metricas de Trafico", dashboard)

        # 3. analisis cada 15 frames
        if contador_frames % 15 == 0:
            print(f"\n--- FRAME {contador_frames} ---")
            print(f"Vehiculos: {analisis['n_vehiculos']} | Densidad: {analisis['densidad']}")
            print(f"Patron: {patron} | Cambio: {cambio}")
            print(f"Analisis Espacial: {analisis['n_clusters']} Clusters detectados")
            anterior_analisis = analisis

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    else:
        print("Fin del video.")
        break

cap.release()
cv2.destroyAllWindows()

