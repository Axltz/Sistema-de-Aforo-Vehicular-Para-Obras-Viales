
def interpret_traffic(metrics):

    occupancy = metrics["spatial_occupancy"]
    speed = metrics["average_speed"]
    distance = metrics["average_distance"]
    compactness = metrics["compactness"]


    if occupancy > 0.6 and speed < 10:
        return {
            "state": "congested",
            "description": "Trafico muy lento y saturado"
        }

    if occupancy > 0.3 and compactness > 1.5:
        return {
            "state": "medium",
            "description": "Flujo moderado de vehiculos"
        }

    return {
        "state": "fluid",
        "description": "Trafico fluido"
    }