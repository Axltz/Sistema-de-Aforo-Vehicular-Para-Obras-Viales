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
    # SECCION 1: AFORO Y FLUJO
    texto_dashboard(dashboard, "ESTADISTICAS DE FLUJO", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    texto_dashboard(dashboard, f"Vehiculos en pantalla: {metricas.get('total_vehicles', 0)}", 20, y_pos, (255, 255, 255), 0.6, 1); y_pos += 30
    texto_dashboard(dashboard, f"Vehiculos que han cruzado: {metricas['total_count']}", 20, y_pos, (0, 255, 0), 0.6, 2); y_pos += 30
    texto_dashboard(dashboard, f"Tasa actual: {metricas.get('flujo_por_minuto', 0)} vehs/min", 20, y_pos, (255, 255, 0), 0.6, 2); y_pos += 50

    # SECCION 2: DIAGNOSTICO DE LA VIA
    texto_dashboard(dashboard, "ESTADO GENERAL DEL TRAFICO", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    texto_dashboard(dashboard, f"{metricas['fluidez_avance']}", 20, y_pos, (255, 255, 255), 0.65, 2); y_pos += 30
    texto_dashboard(dashboard, f"Comportamiento: {metricas['velocidad_marcha']}", 20, y_pos, (150, 150, 150), 0.5, 1); y_pos += 50

    # SECCION 3: EVENTOS EN PISTA (Grupos y Congestión)
    texto_dashboard(dashboard, "MONITOR DE EVENTOS Y AGRUPACIONES", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    
    if metricas.get("alerta_embotellamiento"):
        # Alerta visual parpadeante
        color_alerta = (0, 0, 255) if int(cv2.getTickCount() / cv2.getTickFrequency() * 2) % 2 == 0 else (0, 100, 255)
        cv2.rectangle(dashboard, (10, y_pos-20), (390, y_pos+10), color_alerta, -1)
        texto_dashboard(dashboard, "¡EMBOTELLAMIENTO DETECTADO!", 60, y_pos, (255, 255, 255), 0.6, 2)
    y_pos += 30

    metricas_congestiones = metricas.get("cluster_metrics", [])
    if not metricas_congestiones:
        texto_dashboard(dashboard, "No hay agrupaciones de riesgo.", 20, y_pos, (0, 255, 0), 0.5); y_pos += 25
    else:
        for i, data_grupo in enumerate(metricas_congestiones):
            nombre_grupo = data_grupo["nombre"]
            color_grupo = [(255,100,0), (0,150,255), (100,0,255), (0,255,150)][i%4]
            # Formato: "Grupo de Vehiculos: 4 vehs - Avanzando"
            estado_txt = "Detenidos (Riesgo ALTO)" if data_grupo['riesgo'] == "ALTO" else "Avanzando"
            texto_dashboard(dashboard, f"{nombre_grupo}: {data_grupo['conteo']} vehs - {estado_txt}", 20, y_pos, color_grupo, 0.45, 1); y_pos += 25

    # CONTROLES DEL SISTEMA (Pie de página)
    cv2.putText(dashboard, "CONTROLES:", (20, 640), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
    cv2.putText(dashboard, "[E] Exportar JSON", (20, 665), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 1)
    cv2.putText(dashboard, "[Q] Salir del Sistema", (20, 685), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)

    # VISUALES EN VIDEO PRINCIPAL (Línea de Aforo - Diseño Láser de Neón)
    linea_aforo = resultado_analisis["line"]
    if linea_aforo and linea_aforo["start"] != (0,0):
        p1, p2 = linea_aforo["start"], linea_aforo["end"]
        # Capa 1: Resplandor exterior (Neon Magenta)
        cv2.line(frame, p1, p2, (180, 0, 255), 6, cv2.LINE_AA)
        # Capa 2: Resplandor interior (Cyan Eléctrico)
        cv2.line(frame, p1, p2, (255, 255, 0), 3, cv2.LINE_AA)
        # Capa 3: Núcleo brillante (Blanco Puro)
        cv2.line(frame, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Etiqueta estética flotante tipo "HUD" militar
        txt_linea = "ZONA DE AFORO ACTIVA"
        (w, h), _ = cv2.getTextSize(txt_linea, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        lx, ly = p1[0] + 15, p1[1] - 10
        cv2.rectangle(frame, (lx - 4, ly + 4), (lx + w + 4, ly - h - 4), (20, 20, 20), -1)
        cv2.rectangle(frame, (lx - 4, ly + 4), (lx + w + 4, ly - h - 4), (255, 255, 0), 1)
        cv2.putText(frame, txt_linea, (lx, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    # Diccionario rápido para buscar el (X, Y) de cualquier vehículo por su ID
    posiciones_centros = {v["id"]: v["center"] for v in vehiculos_detectados}
    
    # 2. Dibujar Zonas de Congestión
    vehiculos_en_peligro = set()
    
    for i, data_grupo in enumerate(metricas_congestiones):
        nombre_grupo = data_grupo["nombre"]
        ids_vehiculos = data_grupo["ids"]
        riesgo = data_grupo["riesgo"]
        
        if riesgo == "ALTO":
            vehiculos_en_peligro.update(ids_vehiculos)
        
        puntos_grupo = [posiciones_centros[vid] for vid in ids_vehiculos if vid in posiciones_centros]
        if puntos_grupo:
            cx = int(np.mean([p[0] for p in puntos_grupo]))
            cy = int(np.min([p[1] for p in puntos_grupo])) - 20
            color_texto = (0, 0, 255) if riesgo == "ALTO" else (255, 150, 0)
            
            # Dibujar etiqueta flotante del grupo
            (w, h), _ = cv2.getTextSize(nombre_grupo, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (cx - 44, cy + 4), (cx - 44 + w + 8, cy - h - 4), (20, 20, 20), -1)
            cv2.rectangle(frame, (cx - 44, cy + 4), (cx - 44 + w + 8, cy - h - 4), color_texto, 1)
            cv2.putText(frame, nombre_grupo, (cx - 40, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # 3. Dibujar Vehículos Individuales (HUD Cyberpunk)
    for v in vehiculos_detectados:
        vid = v["id"]
        cx, cy = v["center"]
        
        # Formatear el ID de forma estética como "#01", "#02", etc.
        tag_id = f"#{vid:02d}"
        
        if vid in vehiculos_en_peligro:
            # VEHÍCULO ATASCADO: Diseño de peligro (Naranja/Rojo Neon con pulsos)
            # Anillo de alerta exterior
            cv2.circle(frame, (cx, cy), 11, (0, 80, 255), 2, cv2.LINE_AA)
            # Anillo exterior parpadeante
            cv2.circle(frame, (cx, cy), 14, (0, 0, 255), 1, cv2.LINE_AA)
            # Centro brillante
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1, cv2.LINE_AA)
            
            # Etiqueta de ID flotante roja con fondo oscuro de alto contraste
            (w, h), _ = cv2.getTextSize(tag_id, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.rectangle(frame, (cx - 15, cy - 20), (cx - 15 + w + 6, cy - 20 - h - 4), (10, 10, 60), -1)
            cv2.rectangle(frame, (cx - 15, cy - 20), (cx - 15 + w + 6, cy - 20 - h - 4), (0, 0, 255), 1)
            cv2.putText(frame, tag_id, (cx - 12, cy - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
        else:
            # VEHÍCULO NORMAL: Diseño premium de flujo libre (Cyan Eléctrico / Blanco)
            # Anillo exterior fino
            cv2.circle(frame, (cx, cy), 7, (255, 255, 0), 2, cv2.LINE_AA)
            # Centro blanco brillante
            cv2.circle(frame, (cx, cy), 3, (255, 255, 255), -1, cv2.LINE_AA)
            
            # Etiqueta de ID flotante cyan con fondo oscuro de alto contraste
            (w, h), _ = cv2.getTextSize(tag_id, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.rectangle(frame, (cx - 15, cy - 16), (cx - 15 + w + 6, cy - 16 - h - 4), (15, 15, 15), -1)
            cv2.rectangle(frame, (cx - 15, cy - 16), (cx - 15 + w + 6, cy - 16 - h - 4), (255, 255, 0), 1)
            cv2.putText(frame, tag_id, (cx - 12, cy - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

    return frame, dashboard
