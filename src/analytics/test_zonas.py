from src.analytics.simulacion_vehiculos import generar_dataset
from src.analytics.zonas import segmentar_dataset

data = generar_dataset(3, 5)
resultado = segmentar_dataset(data)

for frame, vehiculos in resultado.items():
    print(f"\n{frame}:")
    for v in vehiculos:
        print(f"  {v}")