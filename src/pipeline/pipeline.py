import numpy as np
from src.analytics.metrics import calculate_metrics
from src.analytics.clustering import detect_dynamic_lanes 
from src.analytics.graphs import build_proximity_graph
from src.analytics.processing import count_vehicles, calibrate_system

def process_frame(vehiculos_detectados, dimensiones_frame, estado_sistema_aforo):
    grafo_interaccion_espacial = build_proximity_graph(vehiculos_detectados, dimensiones_frame)

    grupos_espaciales_activos = detect_dynamic_lanes(vehiculos_detectados, estado_sistema_aforo, dimensiones_frame, estado_sistema_aforo["orientation"])

    metricas_analisis_vial = calculate_metrics(vehiculos_detectados, grafo_interaccion_espacial, grupos_espaciales_activos, dimensiones_frame, estado_sistema_aforo)

    estado_sistema_aforo["metrics_history"].append(metricas_analisis_vial)
    if len(estado_sistema_aforo["metrics_history"]) > 30:
        estado_sistema_aforo["metrics_history"].pop(0)

    return {
        "metrics": metricas_analisis_vial,
        "clusters": grupos_espaciales_activos,
        "graph": grafo_interaccion_espacial,
        "line": estado_sistema_aforo["line"]
    }
