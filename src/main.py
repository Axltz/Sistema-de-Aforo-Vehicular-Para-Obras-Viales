import cv2

from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.analytics.processing import create_system_state, count_vehicles
import numpy as np
from src.visualization.overlay import draw_overlay



video_path = "data/videos/trafico1.mp4"
cap = cv2.VideoCapture(video_path)



state = create_system_state()



frame_count = 0
result = None

while cap.isOpened():

    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    frame = cv2.resize(frame, (1280, 720))
    frame_count += 1


    vehiculos_sucios = frame_detection(frame)
    
    vehiculos_detectados = []
    for v in vehiculos_sucios:
        vid, curr = v["id"], np.array(v["center"])
        prev = np.array(state["ids_history"].get(vid, curr))
        
        if state["orientation"] == "vertical":
            mov = (curr[1] - prev[1]) * state["flow_direction"]
        else:
            mov = (curr[0] - prev[0]) * state["flow_direction"]
            
        if mov >= 0: # Incluir estáticos e inicio de movimiento
            vehiculos_detectados.append(v)
            
    total_count, line = count_vehicles(vehiculos_detectados, state)

    if frame_count % 10 == 0 or result is None:
        result = process_frame(vehiculos_detectados, frame.shape, state)
        result["metrics"]["total_count"] = total_count

    frame_with_overlay, dashboard = draw_overlay(frame, vehiculos_detectados, result)



    cv2.imshow("Sistema de Trafico - Vista Principal", frame_with_overlay)
    cv2.imshow("Dashboard de Control", dashboard)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()