import json
import os
import time
from datetime import datetime
from src.config import METRICS_LIVE_PATH, LOGS_DIR

def save_metrics_local(metrics, append_to_log=False):
    """
    Guarda las métricas en data/metrics_live.json (sobrescrito)
    y acumula en data/logs/metrics_YYYY-MM-DD.jsonl (historial diario) si append_to_log es True.
    La estructura de datos es 100% compatible con el formato de Supabase anterior.
    """
    # Asegurar que existan los directorios
    os.makedirs(LOGS_DIR, exist_ok=True)
    if METRICS_LIVE_PATH.parent:
        os.makedirs(METRICS_LIVE_PATH.parent, exist_ok=True)
        
    now = datetime.now()
    ts_iso = now.isoformat()
    msg_id = int(time.time() * 1000)
    
    # Estructura unificada compatible con lo que app.js espera
    payload = {
        "id": msg_id,
        "ts": ts_iso,
        "total_count": metrics.get("total_count", 0),
        "data": {
            "total_vehicles": metrics.get("total_vehicles", 0),
            "flujo_por_minuto": metrics.get("flujo_por_minuto", 0.0),
            "interaccion_pct": metrics.get("interaccion_pct", 0.0),
            "fluidez_avance": metrics.get("fluidez_avance", "N/A"),
            "velocidad_marcha": metrics.get("velocidad_marcha", "N/A"),
            "alerta_embotellamiento": metrics.get("alerta_embotellamiento", False),
            "cluster_metrics": []
        }
    }
    
    # Mapear los clusters para mantener compatibilidad
    for c in metrics.get("cluster_metrics", []):
        payload["data"]["cluster_metrics"].append({
            "nombre": c.get("nombre", c.get("name", "")),
            "conteo": c.get("conteo", c.get("count", 0)),
            "riesgo": c.get("riesgo", c.get("risk", "BAJO"))
        })
        
    # 1. Guardar/sobrescribir el estado en vivo
    try:
        with open(METRICS_LIVE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error al escribir metrics_live.json: {e}")
        
    # 2. Acumular en el log histórico diario (.jsonl) solo si corresponde
    if append_to_log:
        fecha_hoy = now.strftime("%Y-%m-%d")
        log_file = LOGS_DIR / f"metrics_{fecha_hoy}.jsonl"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ Error al escribir en el historial jsonl: {e}")


def export_summary_json(metrics):
    """
    Exporta un resumen bonito e instantáneo de la situación actual.
    Se ejecuta cuando el usuario presiona la tecla 'E'.
    """
    export_dir = LOGS_DIR.parent / "json"
    os.makedirs(export_dir, exist_ok=True)
        
    export_file = export_dir / "traffic_data.json"
    
    resumen = {
        "reporte_generado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "aforo_total_acumulado": metrics.get("total_count", 0),
        "tasa_flujo_actual_por_min": metrics.get("flujo_por_minuto", 0),
        "vehiculos_en_escena": metrics.get("total_vehicles", 0),
        "estado_general_via": metrics.get("fluidez_avance", "N/A"),
        "riesgo_de_embotellamiento": metrics.get("alerta_embotellamiento", False)
    }
    
    try:
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(resumen, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error al exportar resumen JSON: {e}")