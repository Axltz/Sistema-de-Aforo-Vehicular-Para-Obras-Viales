import streamlit as st
import cv2
import tempfile
import numpy as np
import zipfile
import io
import datetime

# --- CONFIGURACIÓN DE PÁGINA Y TRUCOS CSS AVANZADOS ---
st.set_page_config(
    page_title="Monitor de Aforo Vial", 
    page_icon="🚦", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
    /* Ocultar SOLO el menú derecho y el botón de Deploy, sin romper la barra lateral */
    #MainMenu {visibility: hidden;}
    [data-testid="stHeaderActionElements"] {display: none;}
    footer {visibility: hidden;}
    
    /* Hacer el encabezado transparente para mantener el botón de la barra lateral visible */
    header {background: transparent !important;}
    
    /* Fondo general más inmersivo */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Estilo de Tarjetas para Contenedores */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    /* Botón PLAY (Verde brillante) */
    div[data-testid="column"]:nth-child(1) button {
        background-color: #198754 !important;
        color: white !important;
        font-weight: 800;
        font-size: 18px;
        width: 100%;
        border-radius: 8px;
        border: 2px solid #146c43 !important;
        transition: 0.3s;
    }
    div[data-testid="column"]:nth-child(1) button:hover {
        background-color: #146c43 !important;
        box-shadow: 0 0 15px rgba(25, 135, 84, 0.5);
    }
    
    /* Botón STOP/PAUSA (Rojo alerta) */
    div[data-testid="column"]:nth-child(2) button {
        background-color: #dc3545 !important;
        color: white !important;
        font-weight: 800;
        font-size: 18px;
        width: 100%;
        border-radius: 8px;
        border: 2px solid #b02a37 !important;
        transition: 0.3s;
    }
    div[data-testid="column"]:nth-child(2) button:hover {
        background-color: #b02a37 !important;
        box-shadow: 0 0 15px rgba(220, 53, 69, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# 1. Importamos tu arquitectura modular
from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.analytics.processing import create_system_state, count_vehicles
from src.visualization.overlay import draw_overlay

# --- INGENIERÍA DE MEMORIA (SESSION STATE) ---
if 'playing' not in st.session_state:
    st.session_state.playing = False
if 'frame_idx' not in st.session_state:
    st.session_state.frame_idx = 0
if 'state' not in st.session_state:
    st.session_state.state = create_system_state()
if 'total_count' not in st.session_state:
    st.session_state.total_count = 0
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'current_video_name' not in st.session_state:
    st.session_state.current_video_name = None
if 'fecha_analisis' not in st.session_state:
    st.session_state.fecha_analisis = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if 'result' not in st.session_state:
    st.session_state.result = None
if 'last_frame' not in st.session_state:
    st.session_state.last_frame = None
if 'last_dashboard' not in st.session_state:
    st.session_state.last_dashboard = None

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("Panel de Control")
    st.markdown("---")
    st.markdown("**1. Fuente de Datos**")
    archivo_video = st.file_uploader("Cargar video de tráfico (.mp4, .avi, .mov)", type=["mp4", "avi", "mov"])
    
    st.markdown("---")
    st.markdown("**Información del Sistema:**")
    st.info("Modelo: YOLOv26\n\nResolución: 720p\n\nModo: Procesamiento en Vivo Optimizado")

# --- ÁREA PRINCIPAL ---
st.title("🚦 Sistema Integral de Aforo Vehicular")
st.markdown("*Analítica de tráfico por computadora en tiempo real.*")
st.markdown("---")

# --- MONITOR DE CAMBIO O ELIMINACIÓN DE FUENTE DE DATOS ---
if archivo_video is not None:
    # Si detecta que subiste un archivo con nombre diferente al guardado en memoria
    if st.session_state.current_video_name != archivo_video.name:
        st.session_state.playing = False
        st.session_state.frame_idx = 0
        st.session_state.state = create_system_state()
        st.session_state.total_count = 0
        st.session_state.historial = []
        st.session_state.result = None
        st.session_state.last_frame = None
        st.session_state.last_dashboard = None
        
        # Almacenar el nuevo video
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(archivo_video.read())
        st.session_state.video_path = tfile.name
        st.session_state.current_video_name = archivo_video.name
        st.session_state.fecha_analisis = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.rerun() # Forzar reinicio de interfaz limpio
else:
    # Si se quitó el video (es None) pero antes había un video registrado, limpiamos todo
    if st.session_state.current_video_name is not None:
        st.session_state.playing = False
        st.session_state.frame_idx = 0
        st.session_state.state = create_system_state()
        st.session_state.total_count = 0
        st.session_state.historial = []
        st.session_state.video_path = None
        st.session_state.current_video_name = None
        st.session_state.result = None
        st.session_state.last_frame = None
        st.session_state.last_dashboard = None
        st.rerun()

# --- CONTROL DE RENDERIZADO DE INTERFAZ ---
if archivo_video is not None:
    # --- BOTONES DE CONTROL ---
    st.markdown("### 🕹️ Controles de Reproducción")
    col_btn1, col_btn2, st_empty = st.columns([1, 1, 4])
    with col_btn1:
        if st.button("▶ INICIAR"):
            st.session_state.playing = True
            st.rerun() 
    with col_btn2:
        if st.button("Ⅱ PAUSAR"):
            st.session_state.playing = False
            st.rerun()
            
    st.write("") 

    # --- LIENZOS WEB EN CONTENEDORES ---
    vista_principal = st.container()
    with vista_principal:
        col1, col2 = st.columns([7, 3]) 
        with col1:
            st.markdown("#### 📹 Feed en Vivo")
            espacio_video = st.empty()
        with col2:
            st.markdown("#### 📊 Telemetría")
            espacio_dashboard = st.empty()

    # --- PROYECCIÓN DE IMAGEN PAUSADA ---
    if st.session_state.last_frame is not None:
        espacio_video.image(st.session_state.last_frame, channels="RGB", use_container_width=True)
    if st.session_state.last_dashboard is not None:
        espacio_dashboard.image(st.session_state.last_dashboard, channels="RGB", use_container_width=True)

    # --- BUCLE DE VIDEO ---
    if st.session_state.playing and st.session_state.video_path:
        cap = cv2.VideoCapture(st.session_state.video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_idx)

        while cap.isOpened() and st.session_state.playing:
            ret, frame = cap.read()
            if not ret:
                st.session_state.playing = False
                break

            frame = cv2.resize(frame, (1280, 720))
            st.session_state.frame_idx += 1

            vehiculos_sucios = frame_detection(frame)
            vehiculos_detectados = []
            for v in vehiculos_sucios:
                vid, curr = v["id"], np.array(v["center"])
                prev = np.array(st.session_state.state["ids_history"].get(vid, curr))
                if st.session_state.state["orientation"] == "vertical":
                    mov = (curr[1] - prev[1]) * st.session_state.state["flow_direction"]
                else:
                    mov = (curr[0] - prev[0]) * st.session_state.state["flow_direction"]
                if mov >= 0: 
                    vehiculos_detectados.append(v)
                    
            conteo_actual, line = count_vehicles(vehiculos_detectados, st.session_state.state)
            st.session_state.total_count = conteo_actual

            if st.session_state.frame_idx % 10 == 0 or st.session_state.result is None:
                st.session_state.result = process_frame(vehiculos_detectados, frame.shape, st.session_state.state)
                st.session_state.result["metrics"]["total_count"] = st.session_state.total_count

            if st.session_state.frame_idx % 10 == 0 and st.session_state.result is not None:
                congestion = st.session_state.result["metrics"].get("congestion_level", "N/A")
                densidad = st.session_state.result["metrics"].get("density", 0)
                st.session_state.historial.append(f"Frame: {st.session_state.frame_idx} | Conteo Acumulado: {st.session_state.total_count} | Densidad: {densidad:.2f} | Congestión: {congestion}\n")

            if st.session_state.frame_idx % 2 == 0:
                frame_with_overlay, dashboard = draw_overlay(frame, vehiculos_detectados, st.session_state.result)
                
                frame_web_opt = cv2.resize(frame_with_overlay, (800, 450)) 
                frame_rgb = cv2.cvtColor(frame_web_opt, cv2.COLOR_BGR2RGB)
                st.session_state.last_frame = frame_rgb
                espacio_video.image(frame_rgb, channels="RGB", use_container_width=True)

                if dashboard is not None:
                    dash_web_opt = cv2.resize(dashboard, (400, int(dashboard.shape[0] * (400 / dashboard.shape[1]))))
                    dashboard_rgb = cv2.cvtColor(dash_web_opt, cv2.COLOR_BGR2RGB)
                    st.session_state.last_dashboard = dashboard_rgb
                    espacio_dashboard.image(dashboard_rgb, channels="RGB", use_container_width=True)

        cap.release()
        
   # --- ZONA DE DESCARGA ---
    if st.session_state.video_path is not None and not st.session_state.playing and st.session_state.frame_idx > 0:
        st.markdown("---")
        st.success("✅ Procesamiento en pausa o finalizado.")
        
        with st.expander("📦 Exportar Resultados del Aforo", expanded=True):
            contenido_txt = f"=== REPORTE DE AFORO VEHICULAR INTELIGENTE ===\n"
            contenido_txt += f"Fecha y Hora: {st.session_state.fecha_analisis}\n"
            # ... (el resto de tu texto original)
            contenido_txt += "".join(st.session_state.historial)
            
            # --- APLICANDO HUFFMAN DIRECTAMENTE ---
            texto_binario, diccionario_codigos = comprimir_texto_huffman(contenido_txt)
            
            # Calculamos métricas para demostrar que funciona
            bits_originales = len(contenido_txt) * 8
            bits_comprimidos = len(texto_binario)
            tasa_compresion = 100 - ((bits_comprimidos / bits_originales) * 100)
            
            st.markdown("#### 🗜️ Resultados de Compresión Huffman (Manual)")
            st.write(f"Tamaño original: **{bits_originales} bits**")
            st.write(f"Tamaño comprimido: **{bits_comprimidos} bits**")
            st.write(f"Ahorro de espacio: **{tasa_compresion:.2f}%**")
            
            # Para exportarlo, guardamos la cadena de bits en un archivo de texto simple
            st.download_button(
                label="📥 Descargar Reporte Comprimido (Bits)",
                data=texto_binario,
                file_name="reporte_huffman.bin",
                mime="text/plain",
                use_container_width=True
            )