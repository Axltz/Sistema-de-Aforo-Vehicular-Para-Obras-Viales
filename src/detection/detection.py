import cv2
from ultralytics import YOLO

print("Cargando la Inteligencia Artificial... (esto puede tomar unos segundos)")
model = YOLO('yolov8n.pt') 

video_path = 'trafico.mp4' 
print(f"Intentando abrir el video: {video_path}")

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"No se encontro el video, Verifica que '{video_path}'")
else:
    print("Video encontrado. Iniciando detección... (Presiona 'q' en el video para salir)")

while cap.isOpened():
    exito, frame = cap.read()
    
    if exito:
        resultados = model(frame, classes=[2, 3, 5, 7])
        
        # POSICIONES EXACTAS
        cajas = resultados[0].boxes
        
        for caja in cajas:
            # 1. Se extrae las coordenadas y las convierte a números enteros (píxeles)
            x1, y1, x2, y2 = caja.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # 2. Se identifica que tipo de vehiculo es
            clase_id = int(caja.cls[0])
            nombre_clase = model.names[clase_id]
            
            # 3. print de las posiciones
            print(f"Posición -> {nombre_clase.upper()}: Esquina Superior Izquierda ({x1}, {y1}) | Esquina Inferior Derecha ({x2}, {y2})")
        
        frame_anotado = resultados[0].plot()
        cv2.imshow("Detección de Vehículos con YOLOv8", frame_anotado)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        print("Fin del video.")
        break

cap.release()
cv2.destroyAllWindows()
