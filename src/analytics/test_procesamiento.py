from procesamiento import procesar_frame, clasificar_trafico, detectar_patron, comparar_frames
import random
import time
import matplotlib.pyplot as plt

def generar_frame(n, con_clusters=False):
    if not con_clusters:
        return [(random.randint(0,600), random.randint(0,400)) for _ in range(n)]
    else:
        # Generar vehículos agrupados (clusters)
        puntos = []
        for _ in range(n // 2):
            # Vehículos dispersos
            puntos.append((random.randint(0,600), random.randint(0,400)))
        
        # Un grupo muy pegado (cluster)
        base_x, base_y = random.randint(100, 500), random.randint(100, 300)
        for _ in range(n // 2):
            puntos.append((base_x + random.randint(-20, 20), base_y + random.randint(-20, 20)))
        return puntos

# Casos de prueba específicos
frames = {
    1: generar_frame(4),             # Bajo tráfico
    2: generar_frame(10),            # Tráfico medio disperso
    3: generar_frame(12, True),      # Tráfico medio con un embotellamiento (cluster)
    4: generar_frame(20, True),      # Tráfico alto con congestión
}

print("\n=== TEST DE MÉTRICAS INTEGRADAS (Sprints 1, 2 y Análisis Espacial) ===\n")

print(f"{'Frame':<6} {'Veh':<6} {'Dens':<6} {'Z1':<4} {'Z2':<4} {'Z3':<4} {'Clust':<6} {'Estado':<35} {'Patron':<25} {'Cambio'}")
print("-" * 140)

anterior = None

for f, vehiculos in frames.items():
    r = procesar_frame(vehiculos)

    estado = clasificar_trafico(r["densidad"], r["dispersion"], r["n_clusters"])
    patron = detectar_patron(r["zonas"])
    cambio = comparar_frames(r, anterior)

    z = r["zonas"]

    print(f"{f:<6} {r['n_vehiculos']:<6} {r['densidad']:<6} {z['Z1']:<4} {z['Z2']:<4} {z['Z3']:<4} {r['n_clusters']:<6} {estado:<35} {patron:<25} {cambio}")

    anterior = r

# --- TEST DE RENDIMIENTO ---
tamanos = [10, 50, 100, 500, 1000]
tiempos = []

print("\n=== RENDIMIENTO DEL ANÁLISIS ESPACIAL ===\n")
print(f"{'Vehículos':<12} {'Tiempo (ms)':<12}")
print("-" * 25)

for n in tamanos:
    total = 0
    for _ in range(10):
        frame = generar_frame(n)
        inicio = time.time()
        procesar_frame(frame)
        fin = time.time()
        total += (fin - inicio)
    
    promedio = (total / 10) * 1000
    tiempos.append((n, promedio))
    print(f"{n:<12} {promedio:<12.4f}")

# Gráfica de Rendimiento
x = [t[0] for t in tiempos]
y = [t[1] for t in tiempos]

plt.figure(figsize=(10, 6))
plt.plot(x, y, marker='o', color='b', linestyle='-')
plt.title("Rendimiento del Algoritmo de Procesamiento")
plt.xlabel("Número de Vehículos (N)")
plt.ylabel("Tiempo de Procesamiento (ms)")
plt.grid(True)
plt.show()
