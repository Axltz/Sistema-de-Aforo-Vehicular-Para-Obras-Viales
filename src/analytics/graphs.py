# ==============================================================================
# graphs.py - GENERADOR DE GRAFOS DE INTERACCIÓN Y PROXIMIDAD
# ==============================================================================
# Este módulo se encarga de modelar el flujo de vehículos en pantalla como un 
# "Grafo de Proximidad" (Red de nodos y conexiones). Cada vehículo representa 
# un nodo y las líneas que los conectan representan relaciones de cercanía física.

import numpy as np

def euclidean_distance(p1, p2):
    """
    Calcula la distancia euclidiana directa (línea recta) entre dos puntos en 2D.
    p1 y p2 son tuplas o listas del tipo (x, y).
    """
    x1, y1 = p1
    x2, y2 = p2
    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance

def build_proximity_graph(detections, frame_shape, factor_distancia=0.05):
    """
    Construye una red (grafo) donde los nodos son los vehículos y se crea una
    arista (conexión) si la distancia euclidiana entre ellos es menor que un
    umbral adaptativo (5% del ancho del video).
    Sirve para alimentar los algoritmos de detección de colisiones e interacción espacial.
    """
    alto, ancho = frame_shape[:2]
    # Distancia umbral máxima para considerar que dos carros interactúan (en píxeles)
    distancia_limite = ancho * factor_distancia
    
    # Inicializamos el grafo con una lista de adyacencia vacía para cada vehículo detectado
    grafo = {v["id"]: [] for v in detections}
    centros = {v["id"]: v["center"] for v in detections}
    lista_ids = list(centros.keys())
    
    # Comparamos todos los pares únicos de vehículos para verificar su distancia
    for i in range(len(lista_ids)):
        for j in range(i + 1, len(lista_ids)):
            p1, p2 = centros[lista_ids[i]], centros[lista_ids[j]]
            
            # Distancia matemática
            distancia = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
            
            # Si están lo suficientemente cerca, creamos una arista bidireccional
            if distancia < distancia_limite:
                grafo[lista_ids[i]].append(lista_ids[j])
                grafo[lista_ids[j]].append(lista_ids[i])
                
    return grafo
