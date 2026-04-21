import cv2
from ultralytics import YOLO
# Importamos la lógica de análisis desde la carpeta correspondiente
from analytics.procesamiento import procesar_vehiculos 

# 1. Configuración del Modelo y Parámetros
model = YOLO("yolov8n.pt")
LINEA_Y = 450  # Posición de la línea virtual (ajustable)

def procesar_sprint_1(frame):
    # 2. Detección de objetos
    # Usamos el modelo cargado para obtener las predicciones del frame actual
    results = model(frame)
    
    lista_vehiculos = []
    conteo_frame = 0
    
    # 3. Procesamiento de detecciones (Generar lista y organizar datos)
    for box in results[0].boxes:
        # Filtramos por clases: 2: auto, 3: moto, 5: bus, 7: camión
        cls = int(box.cls)
        if cls in [2, 3, 5, 7]:
            # Obtener coordenadas de la caja (bounding box)
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            # Calcular el punto central del vehículo
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            
            # Tarea: Generar estructura de datos para el módulo de análisis
            lista_vehiculos.append({"x": cx, "y": cy})
            
            # Tarea: Conteo básico (cuántos hay en este frame)
            conteo_frame += 1
            
            # Dibujar visualización básica de detección
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

    # 4. Tarea: Definir línea virtual de conteo
    # Dibujamos la línea en el frame para identificar la zona de paso
    h, w, _ = frame.shape
    cv2.line(frame, (0, LINEA_Y), (w, LINEA_Y), (0, 0, 255), 3)

    # 5. Ejecutar análisis (Cálculo de flujo y dispersión)
    # Enviamos los datos organizados al módulo de procesamiento
    resultados_analisis = procesar_vehiculos(lista_vehiculos)
    
    # Mostrar resultados en pantalla
    cv2.putText(frame, f"Vehiculos en frame: {conteo_frame}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return frame, lista_vehiculos, resultados_analisis

print("Sprint 1: Módulos de conteo, línea virtual y organización de datos listos.")