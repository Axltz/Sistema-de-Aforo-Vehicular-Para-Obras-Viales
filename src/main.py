# ==============================================================================
# main.py - PUNTO DE ENTRADA DEL SISTEMA (VERSIÓN 100% LOCAL & OFFLINE)
# ==============================================================================
# Este archivo es el "motor" principal. Su trabajo es abrir la fuente de video 
# (archivo .mp4 o webcam), leer los frames, ejecutar la detección optimizada 
# (con frame skipping) y escribir los resultados en archivos JSON/JSONL locales.

import cv2
import numpy as np
import argparse
import sys

from src.config import DEFAULT_VIDEO_PATH, FRAME_SKIP_FACTOR
from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.analytics.processing import create_system_state, count_vehicles, calibrate_system
from src.storage.json_writer import save_metrics_local, export_summary_json
from src.visualization.overlay import draw_overlay

# 1. PARSEAR ARGUMENTOS DE CONSOLA
parser = argparse.ArgumentParser(description="Sistema Inteligente de Aforo Vehicular para Obras Viales")
parser.add_argument("--webcam", action="store_true", help="Usar la webcam en tiempo real en lugar de un archivo de video")
parser.add_argument("--video", type=str, default=DEFAULT_VIDEO_PATH, help="Ruta del archivo de video a procesar")
args = parser.parse_args()

# Seleccionar fuente
if args.webcam:
    video_source = 0
    print("🎥 FUENTE CONFIGURADA: Webcam en tiempo real (Canal 0)")
else:
    video_source = args.video
    print(f"🎬 FUENTE CONFIGURADA: Archivo de video '{video_source}'")

# 2. CARGAR EL VIDEO / CÁMARA
cap = cv2.VideoCapture(video_source)
if not cap.isOpened():
    print(f"❌ Error: No se pudo abrir la fuente de video: {video_source}")
    sys.exit(1)

# 3. INICIALIZAR LA MEMORIA DE RASTREO
state = create_system_state()

frame_count = 0
result = None  # Aquí guardaremos el diagnóstico inteligente de tráfico

# BUCLE PRINCIPAL: Lee y procesa los frames secuencialmente
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        if args.webcam:
            print("⚠️ Se perdió la conexión con la webcam.")
            break
        else:
            # Si el video termina, lo reiniciamos (bucle infinito de demo)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

    # Redimensionar el frame para optimizar visualización y velocidad
    h_orig, w_orig = frame.shape[:2]
    aspect = h_orig / w_orig
    frame = cv2.resize(frame, (1024, int(1024 * aspect)))

    frame_count += 1

    # ==========================================================================
    # PASO A: CONDICIONAL DE CALIBRACIÓN CON SALTO DE FRAMES
    # ==========================================================================
    if not state["calibration_locked"]:
        # Corremos YOLO solo en frames seleccionados para ahorrar recursos
        if frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in state:
            vehiculos_sucios = frame_detection(frame)
            
            # Filtramos por sentido de flujo inicial
            vehiculos_detectados = []
            for v in vehiculos_sucios:
                vid, curr = v["id"], np.array(v["center"])
                prev = np.array(state["ids_history"].get(vid, curr))
                
                if state["orientation"] == "vertical":
                    mov = (curr[1] - prev[1]) * state["flow_direction"]
                else:
                    mov = (curr[0] - prev[0]) * state["flow_direction"]
                    
                if mov >= 0:
                    vehiculos_detectados.append(v)
            state["last_detections"] = vehiculos_detectados
            # Solo guardamos el frame cuando YOLO corrió y hay algo nuevo que mostrar
            cv2.imwrite("data/live_frame.jpg", frame)
        else:
            # Si nos saltamos el frame, heredamos las detecciones previas
            vehiculos_detectados = state["last_detections"]
            
        calibrate_system(vehiculos_detectados, frame.shape, state)
        cv2.putText(frame, f"CALIBRANDO FLUJO... {state['calibration_frames']}/30", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Sistema de Trafico - Vista Principal", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break
        continue

    # ==========================================================================
    # SISTEMA YA CALIBRADO: PROCESAMIENTO OPTIMIZADO CON RECORTE Y SKIP-YOLO
    # ==========================================================================
    # PASO B: RECORTE DEL FRAME (Reduce drásticamente el área que procesa YOLO)
    roi = state["active_roi"]
    frame_recortado = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]
    
    # PASO C: DETECCIÓN CON SALTO DE FRAMES (FRAME SKIPPING)
    yolo_ran_this_frame = (frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in state)
    if yolo_ran_this_frame:
        vehiculos_sucios = frame_detection(frame_recortado)
        
        # Filtramos por dirección de avance
        vehiculos_detectados = []
        for v in vehiculos_sucios:
            vid, curr = v["id"], np.array(v["center"])
            prev = np.array(state["ids_history"].get(vid, curr))
            
            if state["orientation"] == "vertical":
                mov = (curr[1] - prev[1]) * state["flow_direction"]
            else:
                mov = (curr[0] - prev[0]) * state["flow_direction"]
                
            if mov >= 0:
                vehiculos_detectados.append(v)
        state["last_detections"] = vehiculos_detectados
    else:
        # Heredamos las posiciones previas de los autos en el frame de salto
        vehiculos_detectados = state["last_detections"]

    # PASO D: CONTADOR VEHICULAR
    total_count, line = count_vehicles(vehiculos_detectados, state)

    # PASO E: INTELIGENCIA DE TRÁFICO (Cómputo cada 10 frames)
    if frame_count % 10 == 0 or result is None:
        result = process_frame(vehiculos_detectados, frame_recortado.shape, state)
        result["metrics"]["total_count"] = total_count
        
        # GUARDAR LOCALMENTE: Escribe live.json cada 10 frames y acumula jsonl cada 150
        append_log = (frame_count % 150 == 0)
        save_metrics_local(result["metrics"], append_to_log=append_log)

    # PASO F: DIBUJAR CAPAS VISUALES (OVERLAYS)
    frame_with_overlay, dashboard = draw_overlay(frame_recortado, vehiculos_detectados, result)

    # Inicializar tamaño de las pantallas
    if frame_count == 1:
        cv2.namedWindow("Sistema de Trafico - Vista Principal", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Sistema de Trafico - Vista Principal", 800, int(800 * aspect))
        cv2.namedWindow("Dashboard de Control", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Dashboard de Control", 300, 500)

    # Renderizar en pantalla
    cv2.imshow("Sistema de Trafico - Vista Principal", frame_with_overlay)
    cv2.imshow("Dashboard de Control", dashboard)
    # Solo guardar cuando YOLO corrió: el frame cambió visualmente
    if yolo_ran_this_frame:
        cv2.imwrite("data/live_frame.jpg", frame_with_overlay)

    # PASO G: TECLADO DE CONTROL
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break  # Apagar sistema
    elif key == ord('e') or key == ord('E'):
        # Exportación manual de un reporte JSON bonito al presionar 'E'
        if result is not None:
            export_summary_json(result["metrics"])
            print("💾 ¡Resumen consolidado exportado a data/json/traffic_data.json!")

cap.release()
cv2.destroyAllWindows()
print("👋 Sistema apagado correctamente.")