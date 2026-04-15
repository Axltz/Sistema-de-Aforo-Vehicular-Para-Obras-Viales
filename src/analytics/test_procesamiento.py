import time
import random
from procesamiento import procesar_vehiculos

def generar_vehiculos(n):
    return [
        {"x": random.randint(0, 100), "y": random.randint(0, 100)}
        for _ in range(n)
    ]

tamanos = [100, 300, 500, 1000]

print("\n--- PRUEBAS DE RENDIMIENTO ---\n")

for n in tamanos:
    vehiculos = generar_vehiculos(n)

    inicio = time.time()

    resultado = procesar_vehiculos(vehiculos)

    fin = time.time()

    tiempo = fin - inicio

    print(f"n = {n}")
    print(f"Tiempo = {tiempo:.6f} s")
    print(f"Resultado = {resultado}")
    print("----------------------")