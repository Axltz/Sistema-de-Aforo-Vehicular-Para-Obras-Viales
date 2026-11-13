# ==============================================================================
# pipeline.py - CENTRAL ANALYTICAL PROCESSING PIPELINE
# ==============================================================================
# This module is the "connection hub" that unifies all the analytical
# sub-modules. It receives raw YOLO detections and sequentially orchestrates the
# proximity graph, vehicle clustering and road calculations.

from src.analytics.clustering import detect_traffic_clusters
from src.analytics.graphs import build_proximity_graph
from src.analytics.metrics import calculate_metrics


def process_frame(detections, frame_dimensions, traffic_state):
    """
    Orchestrates the full road-intelligence flow on every processed frame:
      Step 1: Build the proximity graph between vehicles (connections).
      Step 2: Detect physical clusters (DBSCAN clustering).
      Step 3: Perform the physical traffic calculations (flow, density, alerts).
      Step 4: Manage the rolling metrics history for dynamic analysis.
    """
    # Step 1: Map which vehicles are close to each other using proximity graphs
    spatial_interaction_graph = build_proximity_graph(detections, frame_dimensions)

    # Step 2: Identify platoons or traffic jams with DBSCAN
    active_spatial_clusters = detect_traffic_clusters(detections, frame_dimensions)

    # Step 3: Calculate the qualitative road state and per-minute flow rates
    traffic_metrics = calculate_metrics(
        detections,
        spatial_interaction_graph,
        active_spatial_clusters,
        frame_dimensions,
        traffic_state
    )

    # Step 4: Append the metrics to the internal history and keep it bounded
    # (max 30 frames). This prevents memory leaks and allows comparing
    # short-term dynamic variations.
    traffic_state["metrics_history"].append(traffic_metrics)
    if len(traffic_state["metrics_history"]) > 30:
        traffic_state["metrics_history"].pop(0)

    # Return a unified dictionary ready to be painted on the monitor
    return {
        "metrics": traffic_metrics,
        "clusters": active_spatial_clusters,
        "graph": spatial_interaction_graph,
        "line": traffic_state["line"]
    }
