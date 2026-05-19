# ==============================================================================
# main.py - PUNTO DE ENTRADA DEL SISTEMA
# ==============================================================================
# Este archivo es el "motor" principal. Su trabajo es abrir el video, leer los
# frames uno por uno, y mandar llamar a todos los demás módulos (detección, conteo, 
# inteligencia, gráficas) en el orden correcto.

import cv2
import numpy as np

from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.analytics.processing import create_system_state, count_vehicles, calibrate_system
from src.storage.json_writer import save_metrics_to_json
from src.visualization.overlay import draw_overlay

# 1. CARGAR EL VIDEO
video_path = "data/videos/trafico3.mp4"
cap = cv2.VideoCapture(video_path)

# 2. INICIALIZAR LA MEMORIA
# 'state' es un diccionario que actúa como el cerebro a corto plazo del sistema.
# Guarda el conteo total, el historial de posiciones de los autos, la línea de cruce, etc.
state = create_system_state()

frame_count = 0
result = None # Aquí guardaremos el diagnóstico inteligente de tráfico

# BUCLE PRINCIPAL: Se repite infinitamente hasta que se acabe el video o presiones 'Q'
while cap.isOpened():

    # Leer un frame (una fotografía instantánea del video)
    ret, frame = cap.read()
    if not ret:
        # Si el video termina, lo reiniciamos al inicio (bucle infinito para pruebas)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # Redimensionar el video para que no sea muy pesado para la computadora
    h_orig, w_orig = frame.shape[:2]
    aspect = h_orig / w_orig
    frame = cv2.resize(frame, (1024, int(1024 * aspect)))

    frame_count += 1

    # PASO A: CONDICIONAL DE CALIBRACIÓN O DETECCIÓN CON RECORTE PREVIO
    if not state["calibration_locked"]:
        # Durante la calibración, usamos todo el frame original para encontrar por dónde pasan los autos
        vehiculos_sucios = frame_detection(frame)
        
        # Filtramos por sentido del flujo crudo
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
                
        calibrate_system(vehiculos_detectados, frame.shape, state)
        cv2.putText(frame, f"CALIBRANDO FLUJO... {state['calibration_frames']}/30", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("Sistema de Trafico - Vista Principal", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        continue

    # ==========================================================================
    # SISTEMA YA CALIBRADO: PROCESAMIENTO OPTIMIZADO CON RECORTE PRE-YOLO
    # ==========================================================================
    # PASO B: RECORTE DEL FRAME (Reducimos el tamaño de la imagen que procesará YOLO)
    roi = state["active_roi"]
    frame_recortado = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]
    
    # PASO C: YOLO EN IMAGEN RECORTADA (Mucho más veloz y preciso)
    vehiculos_sucios = frame_detection(frame_recortado)
    
    # Filtramos los vehículos (en coordenadas del recorte)
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

    # PASO D: CONTADOR (Usa la línea adaptativa ya convertida a coordenadas de recorte)
    total_count, line = count_vehicles(vehiculos_detectados, state)

    # PASO E: INTELIGENCIA DE TRÁFICO (El Cerebro)
    # Corre sobre las coordenadas del recorte
    if frame_count % 10 == 0 or result is None:
        result = process_frame(vehiculos_detectados, frame_recortado.shape, state)
        result["metrics"]["total_count"] = total_count
        
        # REGISTRO HISTÓRICO EN SEGUNDO PLANO
        if frame_count % 150 == 0:
            save_metrics_to_json(result["metrics"])

    # PASO F: PINTAR LA PANTALLA
    # Todo está en coordenadas locales del recorte, no requiere transformaciones
    frame_with_overlay, dashboard = draw_overlay(frame_recortado, vehiculos_detectados, result)

    # Inicializar el tamaño de las ventanas la primera vez
    if frame_count == 1:
        cv2.namedWindow("Sistema de Trafico - Vista Principal", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Sistema de Trafico - Vista Principal", 800, int(800 * aspect))
        cv2.namedWindow("Dashboard de Control", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Dashboard de Control", 300, 500)

    # Mostrar en el monitor
    cv2.imshow("Sistema de Trafico - Vista Principal", frame_with_overlay)
    cv2.imshow("Dashboard de Control", dashboard)

    # PASO G: ESCUCHAR EL TECLADO
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break # Apagar el programa
    elif key == ord('e') or key == ord('E'):
        # Al presionar 'E', extrae el último diagnóstico y lo guarda en JSON
        from src.storage.json_writer import export_summary_json
        if result is not None:
            export_summary_json(result["metrics"])
            print("¡Resumen exportado exitosamente a data/json/traffic_data.json!")

cap.release()
cv2.destroyAllWindows()