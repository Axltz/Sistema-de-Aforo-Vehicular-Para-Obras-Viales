from procesamiento import procesar_frame, clasificar_trafico, detectar_patron, comparar_frames
import random
import time
import matplotlib.pyplot as plt


def generar_frame(n):
    return [(random.randint(0,600), random.randint(0,400)) for _ in range(n)]


frames = {
    1: generar_frame(6), 
    2: generar_frame(2),
    3: generar_frame(16),
}


print("\n=== MÉTRICAS COMPLETAS ===\n")

print(f"{'Frame':<6} {'Veh':<6} {'Dens':<6} {'Z1':<4} {'Z2':<4} {'Z3':<4} {'Disp':<12} {'Estado':<28} {'Patrón':<28} {'Cambio'}")
print("-" * 130)

anterior = None

for f, vehiculos in frames.items():
    r = procesar_frame(vehiculos)

    estado = clasificar_trafico(r["densidad"], r["dispersion"])
    patron = detectar_patron(r["zonas"])  
    cambio = comparar_frames(r, anterior)

    z = r["zonas"]

    print(f"{f:<6} {r['n_vehiculos']:<6} {r['densidad']:<6} {z['Z1']:<4} {z['Z2']:<4} {z['Z3']:<4} {r['dispersion']:<12.2f} {estado:<28} {patron:<28} {cambio}")

    anterior = r


tamanos = [100, 500, 1000, 2000]
tiempos = []

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


print("\n=== RENDIMIENTO ===\n")

print(f"{'Vehículos':<12} {'Tiempo (ms)':<12}")
print("-" * 25)

for t in tiempos:
    print(f"{t[0]:<12} {t[1]:<12.4f}")


x = [t[0] for t in tiempos]
y = [t[1] for t in tiempos]

plt.plot(x, y, marker='o')
plt.xlabel("Número de vehículos")
plt.ylabel("Tiempo (ms)")
plt.title("Rendimiento del procesamiento por frame")
plt.show()