import numpy as np

def calculate_spatial_occupancy(detections,frame_shape):

    height, width = frame_shape[:2]
    frame_area = width * height

    occupied_area = 0


    for detection in detections:

        x1, y1, x2, y2 = detection["bbox"]
        box_width = x2 - x1
        box_height = y2 - y1
        box_area = box_width * box_height
        occupied_area += box_area


    if frame_area == 0:
        return 0
    occupancy = occupied_area / frame_area

    return occupancy



def calculate_average_speed(state):

    speeds = []

    for trajectory in state["trajectories"].values():

        if len(trajectory) < 2:
            continue


        x1, y1 = trajectory[-2]
        x2, y2 = trajectory[-1]


        distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        speeds.append(distance)

    if len(speeds) == 0:
        return 0
    average_speed = np.mean(speeds)

    return average_speed



def calculate_average_distance( graph,detections):
    centers = {}

    for detection in detections:

        vehicle_id = detection["id"]
        centers[vehicle_id] = detection["center"]

    distances = []


    for vehicle_id, neighbors in graph.items():
        center_a = centers.get(vehicle_id)
        if center_a is None:
            continue
        for neighbor_id in neighbors:

            center_b = centers.get(neighbor_id)
            if center_b is None:
                continue

            x1, y1 = center_a
            x2, y2 = center_b


            distance = np.sqrt((x2 - x1) ** 2 +(y2 - y1) ** 2)
            distances.append(distance)


    if len(distances) == 0:

        return 0

    average_distance = np.mean(distances)

    return average_distance


def calculate_compactness(graph):
    total_connections = 0

    for neighbors in graph.values():
        total_connections += len(neighbors)
    total_vehicles = len(graph)

    if total_vehicles == 0:

        return 0


    compactness = (

        total_connections /
        total_vehicles
    )

    return compactness



# Conversión a unidades REALES (Estimadas para carretera)
# Ancho carretera: 7m, Largo visible: 50m
PX_TO_M_X = 7.0 / 1280.0 # Basado en ancho estándar 720p/1080p
PX_TO_M_Y = 50.0 / 720.0

def calculate_metrics(vehiculos_flujo_objetivo, grafo_interaccion_espacial, grupos_espaciales_activos, dimensiones_frame, estado_sistema_aforo):
    conteo_vehiculos_escena = len(vehiculos_flujo_objetivo)
    
    # 1. ANALISIS DE GRUPOS (Clustering)
    conteo_grupos_activos = len(grupos_espaciales_activos)
    
    # 2. ANALISIS DE INTERACCION (Saturación Realista)
    # Solo hay saturación si los vehículos están "literalmente pegados" (formando pocos grupos)
    if conteo_vehiculos_escena > 1:
        # Relación Grupos/Vehículos: 1 grupo para todos = 1.0 (máxima saturación)
        # Muchos grupos (uno por auto) = 0.0 (mínima saturación)
        ratio_agrupamiento = 1.0 - (conteo_grupos_activos / conteo_vehiculos_escena)
        
        # Intensidad de conexiones (Grafos)
        total_conexiones = sum([len(conexiones) for conexiones in grafo_interaccion_espacial.values()])
        # Normalización estricta: requiere 4 vecinos para saturar al 100%
        densidad_conexiones = total_conexiones / (conteo_vehiculos_escena * 4)
        
        # Combinamos: saturación alta solo si hay pocos grupos Y muchas conexiones
        porcentaje_interaccion_espacial = (ratio_agrupamiento * 0.7 + densidad_conexiones * 0.3) * 100
    else:
        porcentaje_interaccion_espacial = 0
        
    porcentaje_interaccion_espacial = min(100.0, porcentaje_interaccion_espacial)


    
    # 3. ANALISIS DE MOVIMIENTO (PROMEDIO SOBRE 10 FRAMES)
    historial_metricas = estado_sistema_aforo.get("metrics_history", [])
    posiciones_actuales = {v["id"]: v["center"] for v in vehiculos_flujo_objetivo}
    posiciones_previas = historial_metricas[-1].get("prev_ids_pos", {}) if historial_metricas else {}
    
    desplazamientos = [np.sqrt((posiciones_actuales[vid][0]-posiciones_previas[vid][0])**2 + (posiciones_actuales[vid][1]-posiciones_previas[vid][1])**2) 
                       for vid in posiciones_actuales if vid in posiciones_previas]
    
    # Movimiento en píxeles por cada 10 frames
    mov_total_10_frames = np.mean(desplazamientos) if desplazamientos else 0.0
    # Normalizar a píxeles por frame
    mov_por_frame = mov_total_10_frames / 10.0
    
    # A) VELOCIDAD DE MARCHA (¿Qué tan rápido van?)
    if mov_por_frame > 4.5: velocidad_marcha = "RAPIDA"
    elif mov_por_frame > 1.8: velocidad_marcha = "MODERADA"
    elif mov_por_frame > 0.4: velocidad_marcha = "LENTA"
    else: velocidad_marcha = "MUY LENTA / PARADO"
        
    # B) FLUIDEZ DEL AVANCE (¿Qué tan constante es el flujo?)
    # Un flujo puede ser lento pero constante (bueno para obra)
    if conteo_vehiculos_escena == 0:
        fluidez_avance = "VÍA DESPEJADA"
    elif porcentaje_interaccion_espacial > 70:
        fluidez_avance = "CONGESTIONADO (SATURADO)"
    elif mov_por_frame > 2.0:
        fluidez_avance = "FLUJO CONSTANTE"
    elif mov_por_frame > 0.5:
        fluidez_avance = "FLUJO LENTO PERO CONSTANTE"
    else:
        fluidez_avance = "AVANCE INTERMITENTE"
        
    metricas_analisis_vial = {
        "total_vehicles": conteo_vehiculos_escena,
        "conteo_grupos_activos": conteo_grupos_activos,
        "interaccion_pct": porcentaje_interaccion_espacial,
        "velocidad_marcha": velocidad_marcha,
        "fluidez_avance": fluidez_avance,
        "total_count": estado_sistema_aforo.get("total_count", 0),
        "prev_ids_pos": posiciones_actuales.copy()
    }
    return metricas_analisis_vial




