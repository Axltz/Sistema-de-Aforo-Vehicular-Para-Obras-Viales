import numpy as np
from sklearn.cluster import DBSCAN
from math import sqrt
import time

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
        "flow_direction": 1, # Hacia abajo por defecto
        "line": {"start": (0, 0), "end": (0, 0)} 
    }



def calibrate_system(vehiculos_detectados, dimensiones_frame, estado):
    estado["calibration_frames"] += 1
    alto, ancho = dimensiones_frame[:2]
    
    for v in vehiculos_detectados:
        vid, centro = v["id"], v["center"]
        if vid not in estado["trajectories"]: estado["trajectories"][vid] = []
        estado["trajectories"][vid].append(centro)

    if estado["calibration_frames"] >= 30:
        movimientos = []
        puntos_todos = []
        for t in estado["trajectories"].values():
            if len(t) > 5:
                movimientos.append((t[-1][0]-t[0][0], t[-1][1]-t[0][1]))
                puntos_todos.extend(t)
        
        if not movimientos: return 
        
        pts = np.array(puntos_todos)
        min_x, max_x = np.min(pts[:,0]), np.max(pts[:,0])
        min_y, max_y = np.min(pts[:,1]), np.max(pts[:,1])
        dx_prom = np.mean([m[0] for m in movimientos])
        dy_prom = np.mean([m[1] for m in movimientos])
        
        # 1. Ubicación de la línea y ROI adaptativas según orientación y dirección
        if abs(dy_prom) > abs(dx_prom) * 0.3:
            estado["orientation"] = "vertical"
            estado["flow_direction"] = 1 if dy_prom > 0 else -1
            
            if estado["flow_direction"] == -1: # Subiendo
                # Recortamos ajustado arriba (donde salen) y dejamos margen abajo (de donde vienen)
                margen_top = 20
                margen_bottom = 150
                cy = min_y + 0.2 * (max_y - min_y) # 20% de la trayectoria (cerca del tope de salida)
            else: # Bajando
                # Recortamos ajustado abajo (donde salen) y dejamos margen arriba (de donde vienen)
                margen_top = 150
                margen_bottom = 20
                cy = min_y + 0.8 * (max_y - min_y) # 80% de la trayectoria (cerca de la base de salida, sin tocar abajo)
                
            estado["active_roi"] = {
                "x1": int(max(0, min_x - 150)), "y1": int(max(0, min_y - margen_top)),
                "x2": int(min(ancho, max_x + 150)), "y2": int(min(alto, max_y + margen_bottom))
            }
            line_x1 = estado["active_roi"]["x1"]
            line_x2 = estado["active_roi"]["x2"]
            estado["line"] = {"start": (line_x1, int(cy)), "end": (line_x2, int(cy))}
        else:
            estado["orientation"] = "horizontal"
            estado["flow_direction"] = 1 if dx_prom > 0 else -1
            
            if estado["flow_direction"] == 1: # Derecha
                margen_left = 150
                margen_right = 20
                cx = min_x + 0.8 * (max_x - min_x) # 80% de la trayectoria (cerca de la salida a la derecha)
            else: # Izquierda
                margen_left = 20
                margen_right = 150
                cx = min_x + 0.2 * (max_x - min_x) # 20% de la trayectoria (cerca de la salida a la izquierda)
                
            estado["active_roi"] = {
                "x1": int(max(0, min_x - margen_left)), "y1": int(max(0, min_y - 150)),
                "x2": int(min(ancho, max_x + margen_right)), "y2": int(min(alto, max_y + 150))
            }
            # La línea abarca del extremo superior al extremo inferior del recorte
            line_y1 = estado["active_roi"]["y1"]
            line_y2 = estado["active_roi"]["y2"]
            estado["line"] = {"start": (int(cx), line_y1), "end": (int(cx), line_y2)}
            
        # CONVERTIR LA LÍNEA A COORDENADAS DEL RECORTE DE INMEDIATO
        roi = estado["active_roi"]
        line_start = (estado["line"]["start"][0] - roi["x1"], estado["line"]["start"][1] - roi["y1"])
        line_end = (estado["line"]["end"][0] - roi["x1"], estado["line"]["end"][1] - roi["y1"])
        estado["line"] = {"start": line_start, "end": line_end}
        
        estado["calibration_locked"] = True

def count_vehicles(detections, state):
    if not state.get("calibration_locked"): return 0, None
    
    line = state["line"]
    p1, p2 = np.array(line["start"]), np.array(line["end"])
    
    for d in detections:
        vid, curr = d["id"], np.array(d["center"])
        # Obtener posición anterior antes de que fuera actualizada
        prev = np.array(state["ids_history"].get(vid, curr))        
        # Filtrar por dirección
        if state["orientation"] == "vertical":
            if (curr[1] - prev[1]) * state["flow_direction"] < 0: continue
        else:
            if (curr[0] - prev[0]) * state["flow_direction"] < 0: continue

        def side(p, l1, l2): return np.sign(np.cross(l2-l1, p-l1))
        
        s1, s2 = side(prev, p1, p2), side(curr, p1, p2)
        if s1 != s2: # Contar si cruzó o tocó la línea
            if vid not in state["counted_ids"]:
                state["total_count"] += 1
                state["counted_ids"].add(vid)
                state["crossing_timestamps"].append(time.time())

                
    # Actualizar posiciones para el siguiente frame
    for d in detections:
        vid = d["id"]
        centro = d["center"]
        state["ids_history"][vid] = centro
        
        # MANTENER VIVO EL HISTORIAL DE TRAYECTORIAS
        if vid not in state["trajectories"]:
            state["trajectories"][vid] = []
        state["trajectories"][vid].append(centro)
        # Limitar la memoria a los últimos 30 frames
        if len(state["trajectories"][vid]) > 30:
            state["trajectories"][vid].pop(0)

    # Limpiar timestamps viejos (mantener solo los últimos 60 segundos)
    current_time = time.time()
    state["crossing_timestamps"] = [t for t in state.get("crossing_timestamps", []) if current_time - t <= 60]

    return state["total_count"], line
