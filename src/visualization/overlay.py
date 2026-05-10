import cv2
import numpy as np

from src.analytics.traffic_state import interpret_traffic

def draw_overlay(frame, vehiculos_detectados, resultado_analisis):
    alto, ancho = frame.shape[:2]
    dashboard = np.zeros((700, 400, 3), dtype=np.uint8) + 30
    metricas = resultado_analisis["metrics"]
    
    def texto_dashboard(target, texto, x, y, color=(255, 255, 255), escala=0.6, grosor=1):
        cv2.putText(target, str(texto), (x, y), cv2.FONT_HERSHEY_SIMPLEX, escala, color, grosor)

    # ENCABEZADO
    cv2.rectangle(dashboard, (0, 0), (400, 60), (50, 50, 50), -1)
    texto_dashboard(dashboard, "MONITOR VIAL PROFESIONAL", 20, 40, (0, 255, 255), 0.7, 2)

    y_pos = 100
    # SECCION 1: CONTEO ACUMULADO
    texto_dashboard(dashboard, "AFORO ACUMULADO", 20, y_pos, (200, 200, 200), 0.5); y_pos += 35
    texto_dashboard(dashboard, f"{metricas['total_count']}", 20, y_pos, (0, 255, 0), 1.3, 3); y_pos += 70

    # SECCION 2: AGRUPACION ESPACIAL
    texto_dashboard(dashboard, "GRUPOS EN ESCENA", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    num_grupos = metricas.get("conteo_grupos_activos", 0)
    texto_dashboard(dashboard, f"{num_grupos} Grupos detectados", 20, y_pos, (0, 255, 255), 0.7, 2); y_pos += 50

    # SECCION 3: INTERACCION ENTRE VEHICULOS
    texto_dashboard(dashboard, "DENSIDAD DE INTERACCION", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    pct_interaccion = metricas.get("interaccion_pct", 0)
    estado_interaccion = "FLUIDA" if pct_interaccion < 30 else "DENSA" if pct_interaccion < 70 else "SATURADA"
    color_interaccion = (0, 255, 0) if pct_interaccion < 30 else (0, 255, 255) if pct_interaccion < 70 else (0, 0, 255)
    texto_dashboard(dashboard, f"{estado_interaccion} ({pct_interaccion:.0f}%)", 20, y_pos, color_interaccion, 0.7, 2); y_pos += 60

    # SECCION 4: DINAMICA DE FLUJO
    texto_dashboard(dashboard, "MARCHA Y AVANCE", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    texto_dashboard(dashboard, f"{metricas['velocidad_marcha']} / {metricas['fluidez_avance']}", 20, y_pos, (255, 255, 255), 0.55, 1); y_pos += 40
    texto_dashboard(dashboard, f"Vehiculos en flujo: {metricas['total_vehicles']}", 20, y_pos, (150, 150, 150), 0.4); y_pos += 50

    # VISUALES EN VIDEO PRINCIPAL (Línea de Aforo)
    linea_aforo = resultado_analisis["line"]
    if linea_aforo and linea_aforo["start"] != (0,0):
        cv2.line(frame, linea_aforo["start"], linea_aforo["end"], (0, 0, 255), 4)
        cv2.putText(frame, "LINEA DE AFORO", (linea_aforo["start"][0], linea_aforo["start"][1]-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    posiciones_centros = {v["id"]: v["center"] for v in vehiculos_detectados}
    grafo_interaccion = resultado_analisis["graph"]
    for id_v, vecinos in grafo_interaccion.items():
        if id_v in posiciones_centros:
            p1 = posiciones_centros[id_v]
            for id_n in vecinos:
                if id_n in posiciones_centros:
                    cv2.line(frame, p1, posiciones_centros[id_n], (255, 255, 255), 1)

    for i, (id_grupo, ids_vehiculos) in enumerate(resultado_analisis.get("clusters", {}).items()):
        color_grupo = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)][i%4]
        for vid in ids_vehiculos:
            if vid in posiciones_centros:
                cv2.circle(frame, posiciones_centros[vid], 8, color_grupo, -1)
                cv2.putText(frame, f"ID:{vid}", (posiciones_centros[vid][0]-10, posiciones_centros[vid][1]-15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return frame, dashboard


    return frame, dashboard


