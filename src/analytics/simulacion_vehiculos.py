import random

# CONFIGURACIÓN

NUM_FRAMES = 10
VEHICULOS_POR_FRAME = 5

ANCHO = 640
ALTO = 480

# 1. SIMULAR VEHÍCULOS

def generar_vehiculo(id_vehiculo):
    return {
        "id": id_vehiculo,
        "x": random.randint(0, ANCHO),
        "y": random.randint(0, ALTO)
    }

def simular_frame(frame_num, num_vehiculos, id_inicio):
    vehiculos = []
    for i in range(num_vehiculos):
        vehiculo = generar_vehiculo(id_inicio + i)
        vehiculos.append(vehiculo)
    return vehiculos

# 2. ORGANIZAR POR FRAMES

def generar_dataset(num_frames, vehiculos_por_frame):
    dataset = {}
    id_global = 0

    for frame in range(num_frames):
        vehiculos = simular_frame(frame, vehiculos_por_frame, id_global)
        dataset[f"frame_{frame}"] = vehiculos
        id_global += vehiculos_por_frame

    return dataset

# 3. EJECUCIÓN

if __name__ == "__main__":
    data = generar_dataset(NUM_FRAMES, VEHICULOS_POR_FRAME)

    # Mostrar ejemplo
    for frame, vehiculos in data.items():
        print(f"\n{frame}:")
        for v in vehiculos:
            print(v)