# ==============================================================================
# graphs.py - INTERACTION AND PROXIMITY GRAPH GENERATOR
# ==============================================================================
# This module models the on-screen vehicle flow as a "Proximity Graph" (a
# network of nodes and connections). Each vehicle is a node and the lines that
# connect them represent physical proximity relationships.

import numpy as np


def build_proximity_graph(detections, frame_shape, distance_factor=0.05):
    """
    Builds a network (graph) where nodes are vehicles and an edge (connection)
    is created if the Euclidean distance between them is smaller than an adaptive
    threshold (5% of the video width).
    Feeds the collision-detection and spatial-interaction algorithms.
    """
    height, width = frame_shape[:2]
    distance_threshold = width * distance_factor

    graph = {v["id"]: [] for v in detections}
    centers = {v["id"]: v["center"] for v in detections}
    id_list = list(centers.keys())

    # Compare every unique pair of vehicles to check their distance
    for i in range(len(id_list)):
        for j in range(i + 1, len(id_list)):
            p1, p2 = centers[id_list[i]], centers[id_list[j]]

            distance = np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

            # If they are close enough, create a bidirectional edge
            if distance < distance_threshold:
                graph[id_list[i]].append(id_list[j])
                graph[id_list[j]].append(id_list[i])

    return graph
