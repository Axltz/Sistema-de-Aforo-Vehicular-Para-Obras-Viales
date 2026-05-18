# ==============================================================================
# traffic_events.py - DETECTOR DE ALERTAS Y EVENTOS EN PISTA
# ==============================================================================
# Este módulo se encarga de realizar análisis predictivo a corto plazo.
# Compara el estado del tráfico actual con el estado anterior (hace un segundo)
# para detectar anomalías como frenados bruscos o aglomeraciones repentinas.

def detect_events(prev_metrics, curr_metrics):
    """
    Compara las métricas del frame anterior con las del actual para 
    identificar eventos dinámicos de tráfico (como embotellamientos repentinos).
    """
    events = []

    # EVENTO 1: Congestión Repentina (Aumento rápido en la ocupación espacial)
    # Si el espacio ocupado por los carros sube más del 15% en un instante...
    if curr_metrics["spatial_occupancy"] - prev_metrics["spatial_occupancy"] > 0.15:
        events.append({
            "type": "sudden_congestion",
            "message": "Aumento rapido de congestión"
        })

    # EVENTO 2: Desaceleración Fuerte (Frenazo colectivo)
    # Si la velocidad promedio de los autos cae por debajo del 70% de la velocidad anterior...
    if curr_metrics["average_speed"] < prev_metrics["average_speed"] * 0.7:
        events.append({
            "type": "traffic_slowdown",
            "message": "Reduccion fuerte de velocidad"
        })

    # EVENTO 3: Agrupamiento Rápido de Vehículos
    # Si la densidad de conexiones (compactness) aumenta un 50% o más...
    if curr_metrics["compactness"] > prev_metrics["compactness"] * 1.5:
        events.append({
            "type": "vehicle_clustering",
            "message": "Vehiculos agrupandose"
        })

    return events