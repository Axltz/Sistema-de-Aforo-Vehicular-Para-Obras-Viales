def detect_events(prev_metrics, curr_metrics):

    events = []

    if curr_metrics["spatial_occupancy"] - prev_metrics["spatial_occupancy"] > 0.15:

        events.append({
            "type": "sudden_congestion",
            "message": "Aumento rapido de congestión"
        })

    if curr_metrics["average_speed"] < prev_metrics["average_speed"] * 0.7:

        events.append({
            "type": "traffic_slowdown",
            "message": "Reduccion fuerte de velocidad"
        })

    if curr_metrics["compactness"] > prev_metrics["compactness"] * 1.5:

        events.append({
            "type": "vehicle_clustering",
            "message": "Vehiculos agrupandose"
        })

    return events