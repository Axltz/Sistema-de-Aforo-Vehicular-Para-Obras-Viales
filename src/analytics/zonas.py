# CONFIGURACIÓN DEL PLANO
ANCHO = 640
ALTO = 480

def asignar_zona(x, y):
    # Zona 1 (arriba)
    if y < ALTO / 2:
        return "zona_1"
    
    # Zona 2 (abajo izquierda)
    elif x < ANCHO / 2:
        return "zona_2"
    
    # Zona 3 (abajo derecha)
    else:
        return "zona_3"


def segmentar_frame(vehiculos):
    resultado = []

    for v in vehiculos:
        zona = asignar_zona(v["x"], v["y"])

        vehiculo_con_zona = {
            "id": v["id"],
            "x": v["x"],
            "y": v["y"],
            "zona": zona
        }

        resultado.append(vehiculo_con_zona)

    return resultado


def segmentar_dataset(dataset):
    dataset_zonas = {}

    for frame, vehiculos in dataset.items():
        dataset_zonas[frame] = segmentar_frame(vehiculos)

    return dataset_zonas