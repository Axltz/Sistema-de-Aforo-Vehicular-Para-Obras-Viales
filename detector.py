import cv2
from ultralytics import YOLO

# 1. Cargar el modelo YOLOv8 (descargará un archivo pequeño la primera vez que lo corras)
model = YOLO('yolov8n.pt') 

# 2. Cargar el video a analizar
video_path = 'trafico.mp4' # Cambia esto por la ruta o nombre de tu video
cap = cv2.VideoCapture(video_path)

while cap.isOpened():
    # Leer el video cuadro por cuadro (frame by frame)
    exito, frame = cap.read()
    
    if exito:
        # 3. Analizar el frame actual con la IA
        # El parámetro classes=[2, 3, 5, 7] filtra las detecciones para que solo busque:
        # autos (2), motos (3), autobuses (5) y camiones (7)
        resultados = model(frame, classes=[2, 3, 5, 7])
        
        # 4. Dibujar los cuadros y etiquetas sobre los vehículos detectados
        frame_anotado = resultados[0].plot()
        
        # 5. Mostrar el video con las detecciones en tiempo real
        cv2.imshow("Detección de Vehículos con YOLOv8", frame_anotado)
        
        # Si presionas la tecla 'q', el video se detiene
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        # Si el video termina, salir del bucle
        break

# 6. Liberar los recursos de la computadora
cap.release()
cv2.destroyAllWindows()