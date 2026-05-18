import numpy as np
import time

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


    
    # 3. ANALISIS DE FLUJO (Teoría de Flujo Vehicular: Cruces por Minuto)
    # Reemplazamos la velocidad en píxeles por la Tasa de Flujo real
    timestamps = estado_sistema_aforo.get("crossing_timestamps", [])
    current_time = time.time()
    
    if len(timestamps) >= 2:
        # Tiempo entre el primer cruce recordado y el actual
        tiempo_transcurrido = max(1.0, current_time - timestamps[0])
        flujo_por_minuto = (len(timestamps) / tiempo_transcurrido) * 60.0
    elif len(timestamps) == 1:
        flujo_por_minuto = 1.0 # Al menos 1 cruzó
    else:
        flujo_por_minuto = 0.0
        
    # A) ESTADO DEL FLUJO (¿Qué tan rápido cruzan la línea?)
    if flujo_por_minuto > 30: velocidad_marcha = "FLUJO ALTO"
    elif flujo_por_minuto > 10: velocidad_marcha = "FLUJO MODERADO"
    elif flujo_por_minuto > 0: velocidad_marcha = "FLUJO BAJO"
    else: velocidad_marcha = "SIN FLUJO / DETENIDO"
        
    # B) DIAGNÓSTICO DE LA VÍA (Relación Flujo - Densidad)
    if conteo_vehiculos_escena == 0:
        fluidez_avance = "VIA DESPEJADA"
    elif porcentaje_interaccion_espacial > 70 and flujo_por_minuto < 5:
        fluidez_avance = "CONGESTION SEVERA (Tráfico Detenido)"
    elif porcentaje_interaccion_espacial > 50 and flujo_por_minuto > 20:
        fluidez_avance = "TRAFICO DENSO PERO FLUIDO"
    elif flujo_por_minuto > 10:
        fluidez_avance = "FLUJO LIBRE"
    else:
        fluidez_avance = "TRAFICO LENTO"
        
    metricas_analisis_vial = {
        "total_vehicles": conteo_vehiculos_escena,
        "conteo_grupos_activos": conteo_grupos_activos,
        "interaccion_pct": porcentaje_interaccion_espacial,
        "velocidad_marcha": velocidad_marcha,
        "fluidez_avance": fluidez_avance,
        "flujo_por_minuto": round(flujo_por_minuto, 1),
        "total_count": estado_sistema_aforo.get("total_count", 0),
        "prev_ids_pos": {} # Mantenemos por compatibilidad
    }
    
    # 4. ALERTA DE EMBOTELLAMIENTO (Densidad vs Flujo)
    metricas_congestiones = []
    alerta_activa = False
            
    for i, (nombre_base, vehiculos_en_grupo) in enumerate(grupos_espaciales_activos.items()):
        conteo_grupo = len(vehiculos_en_grupo)
        densidad_grupo = (conteo_grupo / conteo_vehiculos_escena * 100) if conteo_vehiculos_escena > 0 else 0
        
        # NUEVA LÓGICA INFALIBLE: 
        # Si hay autos amontonados (>= 3) PERO nadie está cruzando la línea (Flujo < 5 veh/min)
        # Significa que están atrapados. = EMBOTELLAMIENTO
        if flujo_por_minuto < 5.0 and conteo_grupo >= 3:
            riesgo = "ALTO"
            nombre_final = "Zona de Riesgo"
            alerta_activa = True
        else:
            # Si hay flujo, solo es un grupo avanzando
            riesgo = "BAJO"
            nombre_final = "Grupo de Vehiculos"
            
        metricas_congestiones.append({
            "nombre": nombre_final,
            "conteo": conteo_grupo,
            "densidad_pct": densidad_grupo,
            "riesgo": riesgo,
            "velocidad": round(flujo_por_minuto, 1), # Reutilizamos el campo para mostrar el flujo
            "ids": vehiculos_en_grupo
        })
        
    metricas_analisis_vial["cluster_metrics"] = metricas_congestiones
    metricas_analisis_vial["alerta_embotellamiento"] = alerta_activa
    
    return metricas_analisis_vial





