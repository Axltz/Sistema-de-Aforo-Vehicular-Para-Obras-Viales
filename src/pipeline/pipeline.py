# ==============================================================================
# pipeline.py - TUBERÍA (PIPELINE) CENTRAL DE PROCESAMIENTO ANALÍTICO
# ==============================================================================
# Este módulo es la "central de conexiones" que unifica todos los sub-módulos
# analíticos. Recibe las detecciones crudas de YOLO, y secuencialmente orquesta
# el grafo de proximidad, el agrupamiento de vehículos (clustering) y los cálculos viales.

import numpy as np
from src.analytics.metrics import calculate_metrics
from src.analytics.clustering import detect_traffic_clusters 
from src.analytics.graphs import build_proximity_graph
from src.analytics.processing import count_vehicles, calibrate_system

def process_frame(vehiculos_detectados, dimensiones_frame, estado_sistema_aforo):
    """
    Orquesta el flujo completo de inteligencia vial en cada cuadro procesado:
      Paso 1: Construye el Grafo de Proximidad entre autos (conexiones).
      Paso 2: Detecta agrupamientos físicos (Clustering con DBSCAN).
      Paso 3: Realiza los cálculos físicos de tránsito (Flujo, Densidad, Alertas).
      Paso 4: Gestiona la pila temporal de historial de métricas para análisis dinámico.
    """
    # Paso 1: Mapear qué autos están cerca entre sí usando grafos de proximidad
    grafo_interaccion_espacial = build_proximity_graph(vehiculos_detectados, dimensiones_frame)

    # Paso 2: Identificar pelotones o atascos de vehículos con DBSCAN
    grupos_espaciales_activos = detect_traffic_clusters(vehiculos_detectados, dimensiones_frame)

    # Paso 3: Calcular el estado cualitativo de la vía y tasas de flujo por minuto
    metricas_analisis_vial = calculate_metrics(
        vehiculos_detectados, 
        grafo_interaccion_espacial, 
        grupos_espaciales_activos, 
        dimensiones_frame, 
        estado_sistema_aforo
    )

    # Paso 4: Agregar las métricas al historial interno y mantenerlo limpio (máx 30 frames)
    # Esto previene fugas de memoria y permite comparar variaciones dinámicas a corto plazo.
    estado_sistema_aforo["metrics_history"].append(metricas_analisis_vial)
    if len(estado_sistema_aforo["metrics_history"]) > 30:
        estado_sistema_aforo["metrics_history"].pop(0)

    # Retorna un diccionario unificado con los resultados listos para pintar en el Monitor
    return {
        "metrics": metricas_analisis_vial,
        "clusters": grupos_espaciales_activos,
        "graph": grafo_interaccion_espacial,
        "line": estado_sistema_aforo["line"]
    }
