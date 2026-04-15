def procesar_vehiculos(vehiculos):

    n = len(vehiculos)

    if n == 0:
        return {
            "flujo": 0,
            "actividad_espacial": 0,
            "dispersión": 0,
            "velocidad_simulada": 0
        }

    flujo = n

    velocidades = []
    for v in vehiculos:
        velocidad = (v["x"]**2 + v["y"]**2) ** 0.5
        velocidades.append(velocidad)

    velocidad_simulada = sum(velocidades) / n

    xs = [v["x"] for v in vehiculos]
    ys = [v["y"] for v in vehiculos]

    centro_x = sum(xs) / n
    centro_y = sum(ys) / n

    dispersión = 0
    for v in vehiculos:
        dx = v["x"] - centro_x
        dy = v["y"] - centro_y
        dispersión += (dx**2 + dy**2)

    dispersión /= n

    actividad_espacial = velocidad_simulada / (1 + dispersión)

    return {
        "flujo": flujo,
        "velocidad_simulada": velocidad_simulada,
        "dispersión": dispersión,
        "actividad_espacial": actividad_espacial
    }