import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import distance_matrix

def obtener_zona(x): 
    if x < 200:
        return 1
    elif x < 400:
        return 2
    else:
        return 3
    
def calcular_densidad(n):
    if n <= 5:
        return "Baja"
    elif n <= 15:
        return "Media"
    else:
        return "Alta"

def detectar_patron(zonas):
    total = sum(zonas.values())
    if total == 0:
        return "Sin datos"

    z1, z2, z3 = zonas["Z1"], zonas["Z2"], zonas["Z3"]

    p1 = z1 / total
    p2 = z2 / total
    p3 = z3 / total

    if max(p1, p2, p3) > 0.6:
        if p1 == max(p1, p2, p3):
            return "Alta concentración en carril 1"
        elif p2 == max(p1, p2, p3):
            return "Alta concentración en carril 2"
        else:
            return "Alta concentración en carril 3"

    if max(p1, p2, p3) - min(p1, p2, p3) > 0.3:
        return "Distribución desigual"

    return "Flujo equilibrado"

def clasificar_trafico(densidad, dispersion, n_clusters):
    if densidad == "Alta":
        if n_clusters > 0:
            return "Congestionado (con embotellamientos)"
        return "Congestionado (compacto)"

    elif densidad == "Media":
        if n_clusters > 0:
            return "Moderado con acumulaciones"
        return "Moderado fluido"

    else:
        return "Fluido"

def procesar_frame(vehiculos):   
    n = len(vehiculos)
    if n == 0:
        return {
            "n_vehiculos": 0,
            "densidad": "Baja",
            "zonas": {"Z1": 0, "Z2": 0, "Z3": 0},
            "dispersion": 0,
            "n_clusters": 0
        }

    z1 = z2 = z3 = 0
    for x, y in vehiculos:
        zona = obtener_zona(x)
        if zona == 1: z1 += 1
        elif zona == 2: z2 += 1
        else: z3 += 1

    # Análisis Espacial Avanzado
    puntos = np.array(vehiculos)
    labels = []
    
    # 1. Matriz de distancias y dispersión
    if n > 1:
        dist_mat = distance_matrix(puntos, puntos)
        dispersion = np.sum(dist_mat**2) / (n * (n-1))
        
        # 2. Clustering (DBSCAN) - Detectar grupos a menos de 100px
        clustering = DBSCAN(eps=100, min_samples=2).fit(puntos)
        labels = clustering.labels_
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    else:
        dispersion = 0
        n_clusters = 0
        labels = np.array([-1] * n)

    return {
        "n_vehiculos": n,
        "densidad": calcular_densidad(n),
        "zonas": {"Z1": z1, "Z2": z2, "Z3": z3},
        "dispersion": dispersion,
        "n_clusters": n_clusters,
        "labels": labels
    }

def comparar_frames(actual, anterior):
    if not anterior:
        return "Sin referencia"

    diff = actual["n_vehiculos"] - anterior["n_vehiculos"]
    ratio = diff / (anterior["n_vehiculos"] + 1)

    if ratio > 0.5:
        return "Incremento brusco"
    elif ratio > 0.1:
        return "Incremento gradual"
    elif ratio < -0.5:
        return "Caída brusca"
    elif ratio < -0.1:
        return "Disminución gradual"
    else:
        return "Estable"
