import json
import os
import time
from datetime import datetime

import numpy as np

from src.analytics.huffman import compress_text_huffman
from src.config import LOGS_DIR


def create_system_state():
    return {
        "trajectories": {},
        "total_count": 0,
        "counted_ids": set(),
        "crossing_timestamps": [],
        "ids_history": {},
        "metrics_history": [],
        "calibration_locked": False,
        "calibration_frames": 0,
        "orientation": "vertical",
        "flow_direction": 1,
        "line": {"start": (0, 0), "end": (0, 0)}
    }


def calibrate_system(detections, frame_dimensions, state):
    state["calibration_frames"] += 1
    height, width = frame_dimensions[:2]

    for v in detections:
        vid, center = v["id"], v["center"]
        if vid not in state["trajectories"]:
            state["trajectories"][vid] = []
        state["trajectories"][vid].append(center)

    if state["calibration_frames"] >= 30:
        movements = []
        all_points = []
        for t in state["trajectories"].values():
            if len(t) > 5:
                movements.append((t[-1][0] - t[0][0], t[-1][1] - t[0][1]))
                all_points.extend(t)

        if not movements:
            return

        pts = np.array(all_points)
        min_x, max_x = np.min(pts[:, 0]), np.max(pts[:, 0])
        min_y, max_y = np.min(pts[:, 1]), np.max(pts[:, 1])
        avg_dx = np.mean([m[0] for m in movements])
        avg_dy = np.mean([m[1] for m in movements])

        # 1. Adaptive line and ROI placement based on orientation and direction
        if abs(avg_dy) > abs(avg_dx) * 0.3:
            state["orientation"] = "vertical"
            state["flow_direction"] = 1 if avg_dy > 0 else -1

            if state["flow_direction"] == -1:  # Moving up
                top_margin = 20
                bottom_margin = 150
                cy = min_y + 0.2 * (max_y - min_y)
            else:  # Moving down
                top_margin = 150
                bottom_margin = 20
                cy = min_y + 0.8 * (max_y - min_y)

            state["active_roi"] = {
                "x1": int(max(0, min_x - 150)), "y1": int(max(0, min_y - top_margin)),
                "x2": int(min(width, max_x + 150)), "y2": int(min(height, max_y + bottom_margin))
            }
            line_x1 = state["active_roi"]["x1"]
            line_x2 = state["active_roi"]["x2"]
            state["line"] = {"start": (line_x1, int(cy)), "end": (line_x2, int(cy))}
        else:
            state["orientation"] = "horizontal"
            state["flow_direction"] = 1 if avg_dx > 0 else -1

            if state["flow_direction"] == 1:  # Moving right
                left_margin = 150
                right_margin = 20
                cx = min_x + 0.8 * (max_x - min_x)
            else:  # Moving left
                left_margin = 20
                right_margin = 150
                cx = min_x + 0.2 * (max_x - min_x)

            state["active_roi"] = {
                "x1": int(max(0, min_x - left_margin)), "y1": int(max(0, min_y - 150)),
                "x2": int(min(width, max_x + right_margin)), "y2": int(min(height, max_y + 150))
            }
            line_y1 = state["active_roi"]["y1"]
            line_y2 = state["active_roi"]["y2"]
            state["line"] = {"start": (int(cx), line_y1), "end": (int(cx), line_y2)}

        # IMMEDIATELY CONVERT THE LINE TO CROP COORDINATES
        roi = state["active_roi"]
        line_start = (state["line"]["start"][0] - roi["x1"], state["line"]["start"][1] - roi["y1"])
        line_end = (state["line"]["end"][0] - roi["x1"], state["line"]["end"][1] - roi["y1"])
        state["line"] = {"start": line_start, "end": line_end}

        state["calibration_locked"] = True


def count_vehicles(detections, state):
    if not state.get("calibration_locked"):
        return 0, None

    line = state["line"]
    p1, p2 = np.array(line["start"]), np.array(line["end"])

    for d in detections:
        vid, curr = d["id"], np.array(d["center"])
        prev = np.array(state["ids_history"].get(vid, curr))

        # Filter by direction
        if state["orientation"] == "vertical":
            if (curr[1] - prev[1]) * state["flow_direction"] < 0:
                continue
        else:
            if (curr[0] - prev[0]) * state["flow_direction"] < 0:
                continue

        def side(p, l1, l2):
            return np.sign(np.cross(l2 - l1, p - l1))

        s1, s2 = side(prev, p1, p2), side(curr, p1, p2)
        if s1 != s2:  # Count if it crossed or touched the line
            if vid not in state["counted_ids"]:
                state["total_count"] += 1
                state["counted_ids"].add(vid)
                state["crossing_timestamps"].append(time.time())

    # Update positions for the next frame
    for d in detections:
        vid = d["id"]
        center = d["center"]
        state["ids_history"][vid] = center

        if vid not in state["trajectories"]:
            state["trajectories"][vid] = []
        state["trajectories"][vid].append(center)
        if len(state["trajectories"][vid]) > 30:
            state["trajectories"][vid].pop(0)

    # Clean up old timestamps (keep only the last 60 seconds)
    current_time = time.time()
    state["crossing_timestamps"] = [t for t in state.get("crossing_timestamps", []) if current_time - t <= 60]

    return state["total_count"], line


def export_summary_json_huffman(data, is_history=False):
    export_dir = LOGS_DIR.parent / "json"
    os.makedirs(export_dir, exist_ok=True)

    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")

    if is_history:
        base_name = f"huffman_history_{today_str}_{timestamp_str}"
        content = {
            "report_generated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "FULL_HISTORY",
            "total_records": len(data),
            "records": data
        }
    else:
        base_name = f"huffman_snapshot_{today_str}_{timestamp_str}"
        content = {
            "report_generated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "type": "EXACT_SNAPSHOT",
            "total_accumulated_count": data.get("total_count", 0),
            "current_flow_per_minute": data.get("flow_per_minute", 0),
            "vehicles_in_scene": data.get("total_vehicles", 0),
            "overall_road_state": data.get("flow_state", "N/A"),
            "congestion_risk": data.get("congestion_alert", False)
        }

    export_file = export_dir / f"{base_name}.bin"
    dict_file = export_dir / f"{base_name}_dict.json"

    json_str = json.dumps(content, ensure_ascii=False)
    binary_text, code_table = compress_text_huffman(json_str)

    if not binary_text:
        return

    b = bytearray()
    for i in range(0, len(binary_text), 8):
        byte_chunk = binary_text[i:i + 8].ljust(8, '0')
        b.append(int(byte_chunk, 2))

    try:
        with open(export_file, "wb") as f:
            f.write(bytes(b))
        with open(dict_file, "w", encoding="utf-8") as f:
            json.dump(code_table, f, ensure_ascii=False, indent=2)

        original_bytes = len(json_str.encode('utf-8'))
        compressed_bytes = len(b)
        compression_ratio = 100 - ((compressed_bytes / original_bytes) * 100)

        print("\n" + "=" * 55)
        print(" 🗜️   HUFFMAN-COMPRESSED REPORT (LOCAL) ")
        print("=" * 55)
        print(f" 📂 Binary file:   {export_file.name}")
        print(f" 🔑 Key file:      {dict_file.name}")
        print(f" 📈 Space saved:   {compression_ratio:.2f}%")
        print("=" * 55 + "\n")

        return export_file.name, dict_file.name

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None, None
