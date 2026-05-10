import numpy as np

def euclidean_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    return distance

def build_proximity_graph(detections, frame_shape, factor_distancia=0.05):
    alto, ancho = frame_shape[:2]
    distancia_limite = ancho * factor_distancia
    
    grafo = {v["id"]: [] for v in detections}
    centros = {v["id"]: v["center"] for v in detections}
    lista_ids = list(centros.keys())
    
    for i in range(len(lista_ids)):
        for j in range(i + 1, len(lista_ids)):
            p1, p2 = centros[lista_ids[i]], centros[lista_ids[j]]
            distancia = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
            if distancia < distancia_limite:
                grafo[lista_ids[i]].append(lista_ids[j])
                grafo[lista_ids[j]].append(lista_ids[i])
    return grafo


