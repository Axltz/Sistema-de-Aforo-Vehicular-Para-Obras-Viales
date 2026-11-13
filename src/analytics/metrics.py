# ==============================================================================
# metrics.py - TRAFFIC AND ROAD METRIC CALCULATION ENGINE
# ==============================================================================
# This module converts raw vehicle detections into traffic-engineering
# variables: vehicle count, flow per minute, spatial density and clusters.

import time


def calculate_metrics(target_flow_vehicles, spatial_interaction_graph, active_spatial_clusters, frame_dimensions, traffic_state):
    """
    Brain function that unifies all the physical and logical road variables.
    Calculates:
      1. Real flow rate (vehicles per minute) based on real crossing timestamps.
      2. Qualitative flow diagnosis (Severe Congestion, Slow Traffic, Free Flow, etc.).
      3. Density / spatial interaction percentage on the road.
      4. Cluster classification (moving vehicle groups vs. jammed risk zones).
    """
    vehicles_in_scene = len(target_flow_vehicles)

    # 1. CLUSTER ANALYSIS
    active_cluster_count = len(active_spatial_clusters)

    # 2. INTERACTION ANALYSIS (road saturation)
    if vehicles_in_scene >= 4:
        clustering_ratio = 1.0 - (active_cluster_count / vehicles_in_scene)
        total_connections = sum([len(connections) for connections in spatial_interaction_graph.values()])
        connection_density = total_connections / (vehicles_in_scene * 4)
        spatial_interaction_pct = (clustering_ratio * 0.7 + connection_density * 0.3) * 100
    else:
        # With very few vehicles there can be no saturation, even if they are close.
        spatial_interaction_pct = vehicles_in_scene * 5.0

    spatial_interaction_pct = min(100.0, spatial_interaction_pct)

    # 3. VEHICLE FLOW ANALYSIS (real line crossings per minute)
    timestamps = traffic_state.get("crossing_timestamps", [])
    current_time = time.time()

    if len(timestamps) >= 2:
        elapsed_time = max(1.0, current_time - timestamps[0])
        flow_per_minute = (len(timestamps) / elapsed_time) * 60.0
    elif len(timestamps) == 1:
        flow_per_minute = 1.0
    else:
        flow_per_minute = 0.0

    # TEMPORAL SMOOTHING: average with the flow of recent frames to avoid sudden jumps.
    history = traffic_state.get("metrics_history", [])
    if history:
        previous_flows = [m.get("flow_per_minute", 0) for m in history[-10:]]
        smoothed_flow = (sum(previous_flows) + flow_per_minute) / (len(previous_flows) + 1)
        flow_per_minute = smoothed_flow

    # A) Flow-rate diagnosis (adjusted traffic volume)
    if flow_per_minute > 40:
        flow_level = "HIGH FLOW"
    elif flow_per_minute > 15:
        flow_level = "MODERATE FLOW"
    elif flow_per_minute > 0:
        flow_level = "LOW FLOW"
    else:
        flow_level = "NO FLOW"

    # TRAFFIC TREND
    trend = "STABLE"
    if len(history) > 15:
        old_flow = sum([m.get("flow_per_minute", 0) for m in history[:5]]) / 5
        recent_flow = sum([m.get("flow_per_minute", 0) for m in history[-5:]]) / 5
        if recent_flow > old_flow * 1.2:
            trend = "INCREASING"
        elif recent_flow < old_flow * 0.8:
            trend = "DECREASING"

    # B) Qualitative road diagnosis (relaxed, realistic thresholds)
    if vehicles_in_scene == 0:
        flow_state = "CLEAR ROAD"
    elif spatial_interaction_pct > 80 and flow_per_minute < 3:
        flow_state = "SEVERE CONGESTION"
    elif spatial_interaction_pct > 60 and flow_per_minute > 15:
        flow_state = "DENSE / FLUID TRAFFIC"
    elif flow_per_minute > 15:
        flow_state = "FREE FLOW"
    else:
        flow_state = "MODERATE TRAFFIC"

    traffic_metrics = {
        "total_vehicles": vehicles_in_scene,
        "active_cluster_count": active_cluster_count,
        "spatial_interaction_pct": spatial_interaction_pct,
        "flow_level": flow_level,
        "flow_state": flow_state,
        "flow_per_minute": round(flow_per_minute, 1),
        "total_count": traffic_state.get("total_count", 0),
        "trend": trend,
        "prev_ids_pos": {}
    }

    # 4. CONGESTION AND RISK-GROUP MONITORING
    cluster_metrics = []
    congestion_alert = False

    for vehicles_in_group in active_spatial_clusters.values():
        group_count = len(vehicles_in_group)
        group_density = (group_count / vehicles_in_scene * 100) if vehicles_in_scene > 0 else 0

        # Smarter risk: requires 4+ vehicles and very low flow to be a "jam".
        if flow_per_minute < 3.0 and group_count >= 4:
            risk = "HIGH"
            final_name = "Traffic Jam"
            congestion_alert = True
        elif group_count >= 3 and flow_per_minute < 10.0:
            risk = "MEDIUM"
            final_name = "Slow Traffic"
        else:
            risk = "LOW"
            final_name = "Moving Platoon"

        cluster_metrics.append({
            "name": final_name,
            "count": group_count,
            "density_pct": group_density,
            "risk": risk,
            "speed": round(flow_per_minute, 1),
            "ids": vehicles_in_group
        })

    traffic_metrics["cluster_metrics"] = cluster_metrics
    traffic_metrics["congestion_alert"] = congestion_alert

    return traffic_metrics
