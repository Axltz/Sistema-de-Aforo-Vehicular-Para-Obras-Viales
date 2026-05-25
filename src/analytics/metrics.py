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

        x1, y1 = trajectory[-2]
        x2, y2 = trajectory[-1]

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
    if conteo_vehiculos_escena >= 4:
        ratio_agrupamiento = 1.0 - (conteo_grupos_activos / conteo_vehiculos_escena)
        total_conexiones = sum([len(conexiones) for conexiones in grafo_interaccion_espacial.values()])
        densidad_conexiones = total_conexiones / (conteo_vehiculos_escena * 4)
        porcentaje_interaccion_espacial = (ratio_agrupamiento * 0.7 + densidad_conexiones * 0.3) * 100
    else:
        # Si hay muy pocos autos, no puede haber saturación, incluso si están muy cerca entre sí.
        porcentaje_interaccion_espacial = conteo_vehiculos_escena * 5.0
        
    porcentaje_interaccion_espacial = min(100.0, porcentaje_interaccion_espacial)

    # 3. ANÁLISIS DE FLUJO VEHICULAR (Cruces de línea reales por Minuto)
    timestamps = estado_sistema_aforo.get("crossing_timestamps", [])
    current_time = time.time()
    
    if len(timestamps) >= 2:
        tiempo_transcurrido = max(1.0, current_time - timestamps[0])
        flujo_por_minuto = (len(timestamps) / tiempo_transcurrido) * 60.0
    elif len(timestamps) == 1:
        flujo_por_minuto = 1.0
    else:
        flujo_por_minuto = 0.0
        
    # SUAVIDAD TEMPORAL: Promediar con el flujo de los últimos frames para evitar saltos bruscos
    historial = estado_sistema_aforo.get("metrics_history", [])
    if historial:
        flujos_previos = [m.get("flujo_por_minuto", 0) for m in historial[-10:]]
        flujo_suavizado = (sum(flujos_previos) + flujo_por_minuto) / (len(flujos_previos) + 1)
        flujo_por_minuto = flujo_suavizado

    # A) Diagnóstico de Tasa de Marcha (Volumen de tráfico ajustado)
    if flujo_por_minuto > 40: 
        velocidad_marcha = "FLUJO ALTO"
    elif flujo_por_minuto > 15: 
        velocidad_marcha = "FLUJO MODERADO"
    elif flujo_por_minuto > 0: 
        velocidad_marcha = "FLUJO BAJO"
    else: 
        velocidad_marcha = "SIN FLUJO"
        
    # TENDENCIA DEL TRÁFICO
    tendencia = "ESTABLE"
    if len(historial) > 15:
        flujo_viejo = sum([m.get("flujo_por_minuto", 0) for m in historial[:5]]) / 5
        flujo_reciente = sum([m.get("flujo_por_minuto", 0) for m in historial[-5:]]) / 5
        if flujo_reciente > flujo_viejo * 1.2:
            tendencia = "AUMENTANDO"
        elif flujo_reciente < flujo_viejo * 0.8:
            tendencia = "DISMINUYENDO"

    # B) Diagnóstico Cualitativo de la Vía (Umbrales relajados y realistas)
    if conteo_vehiculos_escena == 0:
        fluidez_avance = "VIA DESPEJADA"
    elif porcentaje_interaccion_espacial > 80 and flujo_por_minuto < 3:
        fluidez_avance = "CONGESTION SEVERA"
    elif porcentaje_interaccion_espacial > 60 and flujo_por_minuto > 15:
        fluidez_avance = "TRAFICO DENSO / FLUIDO"
    elif flujo_por_minuto > 15:
        fluidez_avance = "FLUJO LIBRE"
    else:
        fluidez_avance = "TRAFICO MODERADO"
        
    metricas_analisis_vial = {
        "total_vehicles": conteo_vehiculos_escena,
        "conteo_grupos_activos": conteo_grupos_activos,
        "interaccion_pct": porcentaje_interaccion_espacial,
        "velocidad_marcha": velocidad_marcha,
        "fluidez_avance": fluidez_avance,
        "flujo_por_minuto": round(flujo_por_minuto, 1),
        "total_count": estado_sistema_aforo.get("total_count", 0),
        "tendencia": tendencia,
        "prev_ids_pos": {} 
    }
    
    # 4. MONITOREO DE EMBOTELLAMIENTOS Y GRUPOS DE RIESGO
    metricas_congestiones = []
    alerta_activa = False
            
    for i, (nombre_base, vehiculos_en_grupo) in enumerate(grupos_espaciales_activos.items()):
        conteo_grupo = len(vehiculos_en_grupo)
        densidad_grupo = (conteo_grupo / conteo_vehiculos_escena * 100) if conteo_vehiculos_escena > 0 else 0
        
        # Riesgo más inteligente: requiere 4+ autos y flujo bajísimo para ser "Embotellamiento"
        if flujo_por_minuto < 3.0 and conteo_grupo >= 4:
            riesgo = "ALTO"
            nombre_final = "Embotellamiento"
            alerta_activa = True
        elif conteo_grupo >= 3 and flujo_por_minuto < 10.0:
            riesgo = "MEDIO"
            nombre_final = "Trafico Lento"
        else:
            riesgo = "BAJO"
            nombre_final = "Peloton en Movimiento"
            
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





