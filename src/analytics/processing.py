import numpy as np
from sklearn.cluster import DBSCAN
from math import sqrt

def create_system_state():
    return {
        "trajectories": {},
        "total_count": 0,
        "counted_ids": set(),
        "ids_history": {},
        "metrics_history": [],
        "calibration_locked": True, # Empezar de una
        "orientation": "vertical",
        "flow_direction": 1, # Hacia abajo
        "line": {"start": (50, 600), "end": (900, 600)} # Línea por defecto al fondo
    }


def calibrate_system(detections, frame_shape, state):
    # Usar los primeros 30 frames para determinar el flujo dominante
    state["calibration_frames"] += 1
    h, w = frame_shape[:2]
    
    for d in detections:
        vid, curr = d["id"], d["center"]
        if vid not in state["trajectories"]: state["trajectories"][vid] = []
        state["trajectories"][vid].append(curr)

    if state["calibration_frames"] >= 30:
        # Analizar todas las trayectorias para decidir línea
        movements = []
        for t in state["trajectories"].values():
            if len(t) > 10:
                movements.append((t[-1][0]-t[0][0], t[-1][1]-t[0][1]))
        
        if not movements: return # Seguir calibrando
        
        avg_dx = np.mean([m[0] for m in movements])
        avg_dy = np.mean([m[1] for m in movements])
        
        # 1. Determinar Orientación
        if abs(avg_dy) > abs(avg_dx):
            state["orientation"] = "vertical"
            state["flow_direction"] = 1 if avg_dy > 0 else -1
            # Línea al final del flujo (80% si baja, 20% si sube)
            line_y = int(h * 0.8) if state["flow_direction"] == 1 else int(h * 0.2)
            state["line"] = {"start": (50, line_y), "end": (w - 350, line_y)}
        else:
            state["orientation"] = "horizontal"
            state["flow_direction"] = 1 if avg_dx > 0 else -1
            line_x = int(w * 0.8) if state["flow_direction"] == 1 else int(w * 0.2)
            state["line"] = {"start": (line_x, 50), "end": (line_x, h - 50)}
        
        state["calibration_locked"] = True

def count_vehicles(detections, state):
    if not state.get("calibration_locked"): return 0, None
    
    line = state["line"]
    p1, p2 = np.array(line["start"]), np.array(line["end"])
    
    for d in detections:
        vid, curr = d["id"], np.array(d["center"])
        # Obtener posición anterior antes de que fuera actualizada
        prev = np.array(state["ids_history"].get(vid, curr))
        # (La actualización de ids_history ocurre en pipeline.py antes de llamar a esto)
        # Ojo: si actualizamos antes, el 'prev' siempre será igual a 'curr'.
        # Voy a mover la actualización de ids_history al FINAL de count_vehicles.
        
        # Filtrar por dirección
        if state["orientation"] == "vertical":
            if (curr[1] - prev[1]) * state["flow_direction"] < 0: continue
        else:
            if (curr[0] - prev[0]) * state["flow_direction"] < 0: continue

        def side(p, l1, l2): return np.sign(np.cross(l2-l1, p-l1))
        
        s1, s2 = side(prev, p1, p2), side(curr, p1, p2)
        if s1 != s2 and s1 != 0:
            if vid not in state["counted_ids"]:
                state["total_count"] += 1
                state["counted_ids"].add(vid)
                
    # Actualizar posiciones para el siguiente frame
    for d in detections:
        state["ids_history"][d["id"]] = d["center"]

    return state["total_count"], line