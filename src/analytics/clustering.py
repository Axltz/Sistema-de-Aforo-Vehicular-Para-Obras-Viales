# ==============================================================================
# clustering.py - EL AGRUPADOR (Inteligencia Espacial)
# ==============================================================================
# Este módulo se encarga de analizar las distancias físicas entre todos los
# vehículos en pantalla. Su meta es detectar cuándo los autos están formando un 
# "pelotón" (grupo) porque van muy pegados.

import numpy as np
from sklearn.cluster import DBSCAN

def detect_traffic_clusters(vehiculos_detectados, dimensiones_frame):
    """
    Agrupa vehículos por proximidad física (congestión).
    Sirve para identificar cuellos de botella en zonas de obra.
    """
    if not vehiculos_detectados: 
        return {}
    
    alto, ancho = dimensiones_frame[:2]
    # Extraemos solo las coordenadas (X, Y) de cada auto detectado
    centros = np.array([v["center"] for v in vehiculos_detectados])
    
    # PARAMETRO 1: Epsilon (eps)
    # Define la distancia máxima entre dos autos para considerarlos "vecinos".
    # Usamos el 10% del ancho del video (Agrupa autos a unos 3-4 metros de distancia real)
    eps_distancia = ancho * 0.10 
    
    # PARAMETRO 2: min_samples
    # Define cuántos autos juntos se necesitan para formar un "Grupo".
    # min_samples=3 para ignorar parejitas de autos (eso es tráfico normal).
    # Solo nos importan bultos de 3 o más carros pegados.
    db = DBSCAN(eps=eps_distancia, min_samples=3).fit(centros)
    
    grupos = {}
    for i, etiqueta in enumerate(db.labels_):
        # DBSCAN asigna la etiqueta -1 al "ruido" (autos que van solos o en parejas)
        if etiqueta == -1: continue 
        
        # Si la etiqueta es 0, 1, 2, etc... significa que pertenece a un grupo válido
        nombre_grupo = f"Congestion_{etiqueta}"
        if nombre_grupo not in grupos:
            grupos[nombre_grupo] = []
            
        grupos[nombre_grupo].append(vehiculos_detectados[i]["id"])
        
    return grupos
