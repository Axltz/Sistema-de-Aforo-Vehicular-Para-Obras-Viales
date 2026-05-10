def contar_por_zona(dataset_zonas):
    resultados = {}

    for frame, vehiculos in dataset_zonas.items():
        conteo = {
            "zona_1": 0,
            "zona_2": 0,
            "zona_3": 0
        }

        for v in vehiculos:
            zona = v["zona"]
            conteo[zona] += 1

        resultados[frame] = conteo

    return resultados

