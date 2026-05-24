import json
from src.analytics.huffman import descompresor_huffman
from src.config import LOGS_DIR

def probar_recuperacion():
    # Ubicamos dónde guardaste los archivos comprimidos
    ruta_binario = LOGS_DIR.parent / "json" / "traffic_data_compressed.bin"
    ruta_diccionario = LOGS_DIR.parent / "json" / "traffic_data_dict.json"

    print("Iniciando proceso de descompresión de Huffman...")
    
    try:
        # Llamamos al motor de Huffman para traducir los bits de vuelta a texto
        json_recuperado = descompresor_huffman(ruta_binario, ruta_diccionario)
        
        print("\n" + "="*55)
        print(" 🔓  REPORTE RECUPERADO CON ÉXITO ")
        print("="*55)
        # Imprimimos el resultado formateado y bonito
        print(json.dumps(json_recuperado, indent=4, ensure_ascii=False))
        print("="*55 + "\n")
        
    except FileNotFoundError:
        print("⚠️ Error: No se encontraron los archivos. Asegúrate de correr 'main.py' y presionar 'E' primero.")
    except Exception as e:
        print(f"⚠️ Error inesperado al intentar descomprimir: {e}")

if __name__ == "__main__":
    probar_recuperacion()