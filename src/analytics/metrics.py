# ==============================================================================
# metrics.py - MOTOR DE CÁLCULO DE MÉTRICAS VIALES Y DE TRÁFICO
# ==============================================================================
# Este módulo contiene las funciones matemáticas que calculan el estado del
# tráfico físico. Convierte coordenadas de píxeles en variables de ingeniería
# de tránsito como Aforo, Flujo por Minuto, Densidad Espacial y Agrupamientos.

import numpy as np
import time

def calculate_spatial_occupancy(detections, frame_shape):
    """
    Calcula la Densidad Visual (Ocupación Espacial) en pantalla.
    Suma el área (en píxeles) de todas las cajas delimitadoras de los autos
    y la divide entre el área total de la pantalla. Retorna un valor de 0.0 a 1.0.
    """
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
    """
    Calcula el 'desplazamiento promedio' de los autos activos en el último frame.
    Mide la distancia euclidiana recorrida por el centro de cada vehículo entre
    el cuadro anterior y el actual. Sirve como indicador de velocidad interna.
    """
    speeds = []

    for trajectory in state["trajectories"].values():
        if len(trajectory) < 2:
            continue

        # Posición en t-1 y t
        x1, y1 = trajectory[-2]
        x2, y2 = trajectory[-1]

        # Fórmula de distancia euclidiana: sqrt((x2-x1)^2 + (y2-y1)^2)
        distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        speeds.append(distance)

    if len(speeds) == 0:
        return 0
        
    average_speed = np.mean(speeds)
    return average_speed


def calculate_average_distance(graph, detections):
    """
    Calcula la distancia promedio (en píxeles) entre autos interconectados.
    Utiliza el Grafo de Proximidad para medir la distancia real entre vehículos
    que se encuentran a menos del umbral de cercanía (Epsilon de DBSCAN).
    """
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

            # Distancia euclidiana entre vecinos interconectados
            distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            distances.append(distance)

    if len(distances) == 0:
        return 0

    average_distance = np.mean(distances)
    return average_distance


def calculate_compactness(graph):
    """
    Calcula la Compactación de la red vial (Grado de conectividad).
    Mide cuántas conexiones promedio tiene cada vehículo con sus vecinos.
    Una compactación alta indica que los autos están muy amontonados (potencial atasco).
    """
    total_connections = 0

    for neighbors in graph.values():
        total_connections += len(neighbors)
        
    total_vehicles = len(graph)

    if total_vehicles == 0:
        return 0

    compactness = total_connections / total_vehicles
    return compactness


# Conversión a unidades REALES estimadas (para modelado físico)
PX_TO_M_X = 7.0 / 1280.0 
PX_TO_M_Y = 50.0 / 720.0

def calculate_metrics(vehiculos_flujo_objetivo, grafo_interaccion_espacial, grupos_espaciales_activos, dimensiones_frame, estado_sistema_aforo):
    """
    Función cerebro que unifica todas las variables físicas y lógicas de la vía.
    Calcula:
      1. Tasa de flujo real (vehículos por minuto) basándose en timestamps reales de cruce.
      2. Diagnóstico cualitativo de fluidez (Congestión Severa, Tráfico Lento, Flujo Libre, etc.).
      3. Porcentaje de densidad/interacción espacial en la calzada.
      4. Clasificación de agrupamientos (Grupos de Vehículos en movimiento vs Zonas de Riesgo atascadas).
    """
    conteo_vehiculos_escena = len(vehiculos_flujo_objetivo)
    
    # 1. ANÁLISIS DE GRUPOS (Clustering)
    conteo_grupos_activos = len(grupos_espaciales_activos)
    
    # 2. ANÁLISIS DE INTERACCIÓN (Saturación de la vía)
    # Se evalúa qué tan agrupados físicamente están los autos en el carril.
    if conteo_vehiculos_escena > 1:
        # Ratio de agrupamiento: 1.0 = Todos los autos forman un solo bloque masivo.
        ratio_agrupamiento = 1.0 - (conteo_grupos_activos / conteo_vehiculos_escena)
        
        # Densidad de conexiones del grafo (saturación de vecinos cercanos)
        total_conexiones = sum([len(conexiones) for conexiones in grafo_interaccion_espacial.values()])
        # Normalización estricta: requiere 4 vecinos por auto para saturar al 100% la capacidad de vía
        densidad_conexiones = total_conexiones / (conteo_vehiculos_escena * 4)
        
        # Combinamos: saturación alta si hay alta conectividad y pocos grupos separados
        porcentaje_interaccion_espacial = (ratio_agrupamiento * 0.7 + densidad_conexiones * 0.3) * 100
    else:
        porcentaje_interaccion_espacial = 0
        
    porcentaje_interaccion_espacial = min(100.0, porcentaje_interaccion_espacial)

    # 3. ANÁLISIS DE FLUJO VEHICULAR (Cruces de línea reales por Minuto)
    # En lugar de usar píxeles, evaluamos el comportamiento de cruce en tiempo real.
    timestamps = estado_sistema_aforo.get("crossing_timestamps", [])
    current_time = time.time()
    
    if len(timestamps) >= 2:
        # Tiempo transcurrido entre el primer cruce registrado e histórico
        tiempo_transcurrido = max(1.0, current_time - timestamps[0])
        flujo_por_minuto = (len(timestamps) / tiempo_transcurrido) * 60.0
    elif len(timestamps) == 1:
        flujo_por_minuto = 1.0 # Al menos 1 vehículo ha cruzado la línea
    else:
        flujo_por_minuto = 0.0
        
    # A) Diagnóstico de Tasa de Marcha (Volumen de tráfico)
    if flujo_por_minuto > 30: 
        velocidad_marcha = "FLUJO ALTO"
    elif flujo_por_minuto > 10: 
        velocidad_marcha = "FLUJO MODERADO"
    elif flujo_por_minuto > 0: 
        velocidad_marcha = "FLUJO BAJO"
    else: 
        velocidad_marcha = "SIN FLUJO / DETENIDO"
        
    # B) Diagnóstico Cualitativo de la Vía (Clasificación oficial de Ingeniería de Tránsito)
    if conteo_vehiculos_escena == 0:
        fluidez_avance = "VIA DESPEJADA"
    elif porcentaje_interaccion_espacial > 70 and flujo_por_minuto < 5:
        # Alta densidad y casi nulo avance = Embudo / Congestión
        fluidez_avance = "CONGESTION SEVERA (Tráfico Detenido)"
    elif porcentaje_interaccion_espacial > 50 and flujo_por_minuto > 20:
        # Mucha densidad de autos pero avanzando rápido = Operación densa fluida
        fluidez_avance = "TRAFICO DENSO PERO FLUIDO"
    elif flujo_por_minuto > 10:
        fluidez_avance = "FLUJO LIBRE"
    else:
        fluidez_avance = "TRAFICO LENTO"
        
    # Construimos el diccionario base que consumirá el Dashboard y los archivos JSON
    metricas_analisis_vial = {
        "total_vehicles": conteo_vehiculos_escena,
        "conteo_grupos_activos": conteo_grupos_activos,
        "interaccion_pct": porcentaje_interaccion_espacial,
        "velocidad_marcha": velocidad_marcha,
        "fluidez_avance": fluidez_avance,
        "flujo_por_minuto": round(flujo_por_minuto, 1),
        "total_count": estado_sistema_aforo.get("total_count", 0),
        "prev_ids_pos": {} 
    }
    
    # 4. MONITOREO DE EMBOTELLAMIENTOS Y GRUPOS DE RIESGO
    metricas_congestiones = []
    alerta_activa = False
            
    for i, (nombre_base, vehiculos_en_grupo) in enumerate(grupos_espaciales_activos.items()):
        conteo_grupo = len(vehiculos_en_grupo)
        densidad_grupo = (conteo_grupo / conteo_vehiculos_escena * 100) if conteo_vehiculos_escena > 0 else 0
        
        # Inteligencia de Tránsito:
        # Si un grupo de autos tiene 3 o más vehículos Y la tasa de flujo es bajísima (< 5 veh/min),
        # significa que están atascados o atrapados en obras. Lo declaramos "Zona de Riesgo" (Riesgo ALTO).
        if flujo_por_minuto < 5.0 and conteo_grupo >= 3:
            riesgo = "ALTO"
            nombre_final = "Zona de Riesgo"
            alerta_activa = True
        else:
            # Si hay buen flujo, es simplemente un grupo de autos avanzando normalmente (Riesgo BAJO).
            riesgo = "BAJO"
            nombre_final = "Grupo de Vehiculos"
            
        metricas_congestiones.append({
            "nombre": nombre_final,
            "conteo": conteo_grupo,
            "densidad_pct": densidad_grupo,
            "riesgo": riesgo,
            "velocidad": round(flujo_por_minuto, 1),
            "ids": vehiculos_en_grupo
        })
        
    metricas_analisis_vial["cluster_metrics"] = metricas_congestiones
    metricas_analisis_vial["alerta_embotellamiento"] = alerta_activa
    
    return metricas_analisis_vial





