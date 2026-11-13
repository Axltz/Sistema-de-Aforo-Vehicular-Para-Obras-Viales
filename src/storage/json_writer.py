import json
import os
import time
from datetime import datetime

from src.config import LOGS_DIR, METRICS_LIVE_PATH


def save_metrics_local(metrics, append_to_log=False):
    """
    Saves metrics to data/metrics_live.json (overwritten) and appends to
    data/logs/metrics_YYYY-MM-DD.jsonl (daily history) when append_to_log is True.
    """
    # Ensure the directories exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    if METRICS_LIVE_PATH.parent:
        os.makedirs(METRICS_LIVE_PATH.parent, exist_ok=True)

    now = datetime.now()
    ts_iso = now.isoformat()
    msg_id = int(time.time() * 1000)

    payload = {
        "id": msg_id,
        "ts": ts_iso,
        "total_count": metrics.get("total_count", 0),
        "data": {
            "total_vehicles": metrics.get("total_vehicles", 0),
            "flow_per_minute": metrics.get("flow_per_minute", 0.0),
            "spatial_interaction_pct": metrics.get("spatial_interaction_pct", 0.0),
            "flow_state": metrics.get("flow_state", "N/A"),
            "flow_level": metrics.get("flow_level", "N/A"),
            "congestion_alert": metrics.get("congestion_alert", False),
            "cluster_metrics": []
        }
    }

    # Map the clusters
    for c in metrics.get("cluster_metrics", []):
        payload["data"]["cluster_metrics"].append({
            "name": c.get("name", ""),
            "count": c.get("count", 0),
            "risk": c.get("risk", "LOW")
        })

    # 1. Save/overwrite the live state
    try:
        with open(METRICS_LIVE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error writing metrics_live.json: {e}")

    # 2. Append to the daily history log (.jsonl) only when requested
    if append_to_log:
        today_str = now.strftime("%Y-%m-%d")
        log_file = LOGS_DIR / f"metrics_{today_str}.jsonl"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️ Error writing to the jsonl history: {e}")


def export_summary_json(data, is_history=False):
    """
    Exports a summary (or history) with a timestamp in the filename.
    """
    export_dir = LOGS_DIR.parent / "json"
    os.makedirs(export_dir, exist_ok=True)

    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")

    if is_history:
        # data is a list of records
        export_file = export_dir / f"report_history_{today_str}_{timestamp_str}.json"
        content = {
            "report_generated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "FULL_HISTORY",
            "total_records": len(data),
            "records": data
        }
    else:
        # data is the current metrics object
        export_file = export_dir / f"report_snapshot_{today_str}_{timestamp_str}.json"
        content = {
            "report_generated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "EXACT_SNAPSHOT",
            "total_accumulated_count": data.get("total_count", 0),
            "current_flow_per_minute": data.get("flow_per_minute", 0),
            "vehicles_in_scene": data.get("total_vehicles", 0),
            "overall_road_state": data.get("flow_state", "N/A"),
            "congestion_risk": data.get("congestion_alert", False)
        }

    try:
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
        return export_file.name
    except Exception as e:
        print(f"⚠️ Error exporting the JSON summary: {e}")
        return None
