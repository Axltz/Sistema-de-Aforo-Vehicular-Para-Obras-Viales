import json
import os
import time
from datetime import datetime

def save_metrics_to_json(metrics):
    """
    Guarda las métricas calculadas en un archivo JSON línea por línea (JSONL).
    El archivo se nombra automáticamente por día.
    """
    log_dir = "data/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"metrics_{fecha_hoy}.jsonl")
    
    # Preparamos un diccionario limpio para guardar
    data_to_save = {
        "timestamp": time.time(),
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_vehicles": metrics.get("total_vehicles", 0),
        "total_count": metrics.get("total_count", 0),
        "flow_per_minute": metrics.get("flujo_por_minuto", 0),
        "interaction_density": metrics.get("interaccion_pct", 0),
        "traffic_state": metrics.get("fluidez_avance", "N/A"),
        "congestion_alert": metrics.get("alerta_embotellamiento", False),
        "clusters": []
    }
    
    for data in metrics.get("cluster_metrics", []):
        data_to_save["clusters"].append({
            "name": data["nombre"],
            "count": data["conteo"],
            "risk": data["riesgo"]
        })
        
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(data_to_save) + "\n")

def export_summary_json(metrics):
    """
    Exporta un resumen bonito e instantáneo de la situación actual.
    Se ejecuta cuando el usuario presiona la tecla 'E'.
    """
    export_dir = "data/json"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        
    export_file = os.path.join(export_dir, "traffic_data.json")
    
    resumen = {
        "reporte_generado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "aforo_total_acumulado": metrics.get("total_count", 0),
        "tasa_flujo_actual_por_min": metrics.get("flujo_por_minuto", 0),
        "vehiculos_en_escena": metrics.get("total_vehicles", 0),
        "estado_general_via": metrics.get("fluidez_avance", "N/A"),
        "riesgo_de_embotellamiento": metrics.get("alerta_embotellamiento", False)
    }
    
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=4, ensure_ascii=False)