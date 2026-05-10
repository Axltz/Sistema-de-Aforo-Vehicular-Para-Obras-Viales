import numpy as np
from sklearn.cluster import DBSCAN

def normalize_position(center, frame_shape):
    h, w = frame_shape[:2]
    x,y = center
    nx = x / w
    ny = y / h
    return nx, ny

def normalize_direction(direction):
    dx, dy = direction
    magnitude = np.sqrt(dx**2 + dy**2)
    if magnitude == 0:
        return 0, 0
    ndx = dx / magnitude
    ndy = dy / magnitude
    return ndx, ndy

def detect_dynamic_lanes(vehiculos_detectados, estado_sistema_aforo, dimensiones_frame, orientacion):
    if not vehiculos_detectados: return {}
    
    alto, ancho = dimensiones_frame[:2]
    # Extraer centros de vehículos
    centros = np.array([v["center"] for v in vehiculos_detectados])
    
    # DBSCAN: Agrupa vehículos cercanos (8% del ancho del video)
    # Esto detecta grupos físicos reales, independiente de la resolución
    eps_relativo = ancho * 0.08
    
    db = DBSCAN(eps=eps_relativo, min_samples=1).fit(centros)
    grupos = {}
    for i, etiqueta in enumerate(db.labels_):
        nombre_grupo = f"Grupo_{etiqueta}"
        if nombre_grupo not in grupos: grupos[nombre_grupo] = []
        grupos[nombre_grupo].append(vehiculos_detectados[i]["id"])
        
    return grupos
