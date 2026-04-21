import cv2
from ultralytics import YOLO
from analytics.procesamiento import procesar_vehiculos

# 1. Configuración y variables de estado
model = YOLO("yolov8n.pt")
LINEA_CRUCE_Y = 400      # Línea horizontal para detectar el paso
conteo_total_cruces = 0  # Variable acumulativa para el Sprint 2

def procesar_sprint_2(frame):
    global conteo_total_cruces
    results = model(frame)
    h, w, _ = frame.shape
    
    # Tarea: Dividir el frame en zonas (Izquierda y Derecha)
    limite_x = w // 2
    vehiculos_izquierda = 0
    vehiculos_derecha = 0
    
    datos_para_analisis = []

    # 2. Procesamiento de detecciones reales
    for box in results[0].boxes:
        # Filtrar clases: auto, moto, bus, camión
        if int(box.cls) in [2, 3, 5, 7]:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            # Tarea: Contar vehículos por zona
            if cx < limite_x:
                vehiculos_izquierda += 1
                color_zona = (255, 0, 0) # Azul
            else:
                vehiculos_derecha += 1
                color_zona = (0, 255, 255) # Amarillo

            # Tarea: Detección de cruce por frame
            # Si el centroide pasa por la zona de la línea (margen de 3 píxeles)
            if abs(cy - LINEA_CRUCE_Y) < 3:
                conteo_total_cruces += 1

            # Preparar datos para el módulo de análisis espacial
            datos_para_analisis.append({"x": cx, "y": cy})
            
            # Visualización: Bounding boxes y centros
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color_zona, 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

    # 3. Ejecutar análisis (Cálculo de flujo en tiempo real y dispersión)
    analisis = procesar_vehiculos(datos_para_analisis)

    # 4. Interfaz gráfica básica (Visualización de resultados)
    # Dibujar línea de cruce (Roja)
    cv2.line(frame, (0, LINEA_CRUCE_Y), (w, LINEA_CRUCE_Y), (0, 0, 255), 2)
    # Dibujar división de zonas (Gris)
    cv2.line(frame, (limite_x, 0), (limite_x, h), (150, 150, 150), 1)

    # Etiquetas de datos
    cv2.putText(frame, f"Zona Izq: {vehiculos_izquierda} | Zona Der: {vehiculos_derecha}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Total Cruces: {conteo_total_cruces}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return frame, analisis

print("Sprint 2: Detección de cruces, zonas y visualización integrados.")