import time
import random
from procesamiento import AnalizadorTrafico

def ejecutar_test_realista():
    analizador = AnalizadorTrafico()
    
    header = f"{'FRAME':<6} | {'AUTOS':<5} | {'ESTADO':<10} | {'TENDENCIA':<20} | {'VEL (km/h)':<12} | {'DISPERSIÓN':<12} | {'ACTIVIDAD':<10}"
    print("\n" + header)
    print("-" * len(header))

    for i in range(1, 16):
        n = i * 8  
        
        vehiculos = [
            {
                "x": random.uniform(10, 50), 
                "y": random.uniform(5, 15)
            } for _ in range(n)
        ]
        
        res = analizador.procesar_frame_vehiculo(vehiculos, tiempo_segundos=1.0)
        datos = res['numeros']
        
        print(f"{i:<6} | "
              f"{n:<5} | "
              f"{res['estado']:<10} | "
              f"{res['cambio_frame']:<20} | "
              f"{datos['velocidad_simulada']:<12.2f} | "
              f"{datos['dispersion']:<12.2f} | "
              f"{datos['actividad_espacial']:<10.5f}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    ejecutar_test_realista()