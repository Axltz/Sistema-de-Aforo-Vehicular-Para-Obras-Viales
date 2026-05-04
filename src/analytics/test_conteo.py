from src.analytics.simulacion_vehiculos import generar_dataset
from src.analytics.zonas import segmentar_dataset
from src.analytics.conteo import contar_por_zona

data = generar_dataset(3, 5)
data_zonas = segmentar_dataset(data)
conteo = contar_por_zona(data_zonas)

for frame, zonas in conteo.items():
    print(f"\n{frame}:")
    for zona, cantidad in zonas.items():
        print(f"  {zona}: {cantidad}")