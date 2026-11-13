# ==============================================================================
# clustering.py - THE CLUSTERER (Spatial Intelligence)
# ==============================================================================
# This module analyzes the physical distances between all on-screen vehicles.
# Its goal is to detect when vehicles form a cluster because they are too close.

import numpy as np
from sklearn.cluster import DBSCAN


def detect_traffic_clusters(detections, frame_dimensions):
    """
    Groups vehicles by physical proximity (congestion).
    Helps identify bottlenecks in roadwork zones.
    """
    if not detections:
        return {}

    height, width = frame_dimensions[:2]
    centers = np.array([v["center"] for v in detections])

    # PARAMETER 1: Epsilon (eps)
    # Defines the maximum distance between two vehicles to consider them "neighbors".
    # We use 10% of the video width (groups vehicles ~3-4 meters apart in real distance).
    eps_distance = width * 0.10

    # PARAMETER 2: min_samples
    # Defines how many vehicles together are needed to form a "cluster".
    # min_samples=3 ignores pairs of vehicles (that is normal traffic).
    # We only care about groups of 3 or more closely packed vehicles.
    db = DBSCAN(eps=eps_distance, min_samples=3).fit(centers)

    clusters = {}
    for i, label in enumerate(db.labels_):
        if label == -1:
            continue

        cluster_name = f"Congestion_{label}"
        if cluster_name not in clusters:
            clusters[cluster_name] = []

        clusters[cluster_name].append(detections[i]["id"])

    return clusters
