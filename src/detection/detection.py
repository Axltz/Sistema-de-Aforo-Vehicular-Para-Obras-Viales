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

anterior_analisis = None

while cap.isOpened():
    exito, frame = cap.read()
    
    if exito:
        resultados = model(frame, classes=[2, 3, 5, 7])
        
        cajas = resultados[0].boxes
        centros = []
        
        for caja in cajas:
            x1, y1, x2, y2 = caja.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            centros.append((cx, cy))
            
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

        # --- INTEGRACIÓN CON ANÁLISIS ---
        analisis = procesar_frame(centros)
        estado = clasificar_trafico(analisis["densidad"], analisis["dispersion"], analisis["n_clusters"])
        patron = detectar_patron(analisis["zonas"])
        cambio = comparar_frames(analisis, anterior_analisis)
        
        # --- VISUALIZACIÓN DE MÉTRICAS ---
        y0, dy = 30, 30
        textos = [
            f"Vehiculos: {analisis['n_vehiculos']}",
            f"Estado: {estado}",
            f"Patron: {patron}",
            f"Cambio: {cambio}",
            f"Clusters: {analisis['n_clusters']}"
        ]
        
        for i, line in enumerate(textos):
            y = y0 + i * dy
            cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        frame_anotado = resultados[0].plot()
        # Combinar el frame original (con nuestros puntos y texto) y las anotaciones de YOLO
        # En este caso, simplificaremos usando el frame anotado y añadiendo el texto
        for i, line in enumerate(textos):
            y = y0 + i * dy
            cv2.putText(frame_anotado, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
        cv2.imshow("Sistema Inteligente de Trafico - Aforo y Analisis", frame_anotado)
        
        anterior_analisis = analisis

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        print("Fin del video.")
        break

cap.release()
cv2.destroyAllWindows()

