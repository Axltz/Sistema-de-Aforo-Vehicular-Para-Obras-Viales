import cv2
import time
import numpy as np
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk

# Matplotlib para gráfica en tiempo real embebida en Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.config import DEFAULT_VIDEO_PATH, FRAME_SKIP_FACTOR, LOGS_DIR
from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.analytics.processing import create_system_state, count_vehicles, calibrate_system, export_summary_json_huffman
from src.storage.json_writer import save_metrics_local, export_summary_json
from src.visualization.overlay import draw_overlay
from src.analytics.huffman import descompresor_huffman
import json

class VehicleCounterEngine:
    """Encapsula el loop lógico sin romper el estado continuo de OpenCV"""
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.state = create_system_state()
        self.frame_count = 0
        self.result = None
        self.last_metrics = {}
        
    def restart(self, new_path=None):
        if new_path:
            self.video_path = new_path
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path)
        # El state NO se reinicia para mantener la memoria temporal de autos (opcional, aunque si es otro video, lo ideal es limpiar el state)
        # Para evitar cruces raros entre videos, sí recreamos el state al cambiar de archivo,
        # pero mantenemos el mismo engine si solo se reinicia.
        if new_path:
            self.state = create_system_state()
        else:
            # Si es el mismo video repitiéndose, no borramos el historial para que no dé un salto brusco.
            pass
        self.frame_count = 0
        self.result = None

    def release(self):
        if self.cap:
            self.cap.release()

    def tick(self):
        """Procesa un solo frame y retorna las imágenes y métricas. 
           Lógica intacta de main.py."""
        if not self.cap or not self.cap.isOpened():
            return None, None, self.last_metrics

        ret, frame = self.cap.read()
        if not ret:
            # Loop infinito
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return None, None, self.last_metrics

        h_orig, w_orig = frame.shape[:2]
        aspect = h_orig / w_orig
        frame = cv2.resize(frame, (1024, int(1024 * aspect)))
        self.frame_count += 1

        # PASO A: Calibración
        if not self.state["calibration_locked"]:
            if self.frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in self.state:
                vehiculos_sucios = frame_detection(frame)
                vehiculos_detectados = []
                for v in vehiculos_sucios:
                    vid, curr = v["id"], np.array(v["center"])
                    prev = np.array(self.state["ids_history"].get(vid, curr))
                    if self.state["orientation"] == "vertical":
                        mov = (curr[1] - prev[1]) * self.state["flow_direction"]
                    else:
                        mov = (curr[0] - prev[0]) * self.state["flow_direction"]
                    if mov >= 0:
                        vehiculos_detectados.append(v)
                self.state["last_detections"] = vehiculos_detectados
            else:
                vehiculos_detectados = self.state["last_detections"]
                
            calibrate_system(vehiculos_detectados, frame.shape, self.state)
            cv2.putText(frame, f"CALIBRANDO FLUJO... {self.state['calibration_frames']}/30", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            return frame, None, self.last_metrics

        # PASO B: Recorte
        roi = self.state["active_roi"]
        frame_recortado = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]
        
        # PASO C: Detección con Skip
        yolo_ran_this_frame = (self.frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in self.state)
        if yolo_ran_this_frame:
            vehiculos_sucios = frame_detection(frame_recortado)
            vehiculos_detectados = []
            for v in vehiculos_sucios:
                vid, curr = v["id"], np.array(v["center"])
                prev = np.array(self.state["ids_history"].get(vid, curr))
                if self.state["orientation"] == "vertical":
                    mov = (curr[1] - prev[1]) * self.state["flow_direction"]
                else:
                    mov = (curr[0] - prev[0]) * self.state["flow_direction"]
                if mov >= 0:
                    vehiculos_detectados.append(v)
            self.state["last_detections"] = vehiculos_detectados
        else:
            vehiculos_detectados = self.state["last_detections"]

        # PASO D: Conteo
        total_count, line = count_vehicles(vehiculos_detectados, self.state)

        # PASO E: Métricas (cada 10 frames para no ahogar)
        if self.frame_count % 10 == 0 or self.result is None:
            self.result = process_frame(vehiculos_detectados, frame_recortado.shape, self.state)
            self.result["metrics"]["total_count"] = total_count
            self.last_metrics = self.result["metrics"]

        # PASO F: Overlay Visual (Intacto)
        frame_with_overlay, dashboard_img = draw_overlay(frame_recortado, vehiculos_detectados, self.result)
        
        return frame_with_overlay, dashboard_img, self.last_metrics

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema Inteligente de Aforo Vehicular")
        self.geometry("1400x850")
        self.configure(fg_color="#0b0f19")

        # Variables de control
        self.running = False
        self.engine = None
        self.historial_flujo = []
        self.tiempo_historial = []
        self.historial_completo = []
        self.start_time = time.time()
        
        # Configuración Auto-Log
        self.auto_log_interval = tk.IntVar(value=0) # 0 = Off
        self.last_log_time = time.time()

        self.build_ui()
        self.load_engine(DEFAULT_VIDEO_PATH)
        
        # Iniciar loop asíncrono
        self.update_loop()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=7) # Izquierda 70%
        self.grid_columnconfigure(1, weight=3) # Derecha 30%
        self.grid_rowconfigure(0, weight=1)

        # ----------------- PANEL IZQUIERDO (VIDEO + GRÁFICA) -----------------
        self.left_panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.left_panel.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=7)
        self.left_panel.grid_rowconfigure(1, weight=3)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # Video Label
        self.video_frame = ctk.CTkFrame(self.left_panel, fg_color="black", corner_radius=10)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack(expand=True, fill="both")

        # Gráfica Matplotlib
        self.graph_frame = ctk.CTkFrame(self.left_panel, fg_color="#1f2937", corner_radius=10)
        self.graph_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        self.fig = Figure(figsize=(8, 2.5), dpi=100, facecolor="#1f2937")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1f2937")
        self.ax.tick_params(colors="white")
        for spine in self.ax.spines.values():
            spine.set_color("#374151")
        self.ax.set_title("Flujo Vehicular (vehs/min) en Vivo", color="#00d4ff", fontsize=10)
        self.line, = self.ax.plot([], [], color="#00ff88", linewidth=2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both", padx=5, pady=5)

        # ----------------- PANEL DERECHO (MÉTRICAS + CONTROLES) -----------------
        self.right_panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        
        # Título
        ctk.CTkLabel(self.right_panel, text="MONITOR DE TRÁFICO", font=("Inter", 20, "bold"), text_color="#00d4ff").pack(pady=(20, 5))
        ctk.CTkLabel(self.right_panel, text="SISTEMA INTELIGENTE DE AFORO", font=("Inter", 12), text_color="#9ca3af").pack(pady=(0, 20))

        # Cuadros de Métricas
        self.metrics_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.metrics_container.pack(fill="x", padx=20, pady=5)

        self.lbl_aforo = self.create_metric_box(self.metrics_container, "Aforo Total", "0", "#10b981")
        self.lbl_vehiculos = self.create_metric_box(self.metrics_container, "Vehículos en Escena", "0", "#00ff88")
        self.lbl_flujo = self.create_metric_box(self.metrics_container, "Flujo (vehs/min)", "0.0", "#00d4ff")
        self.lbl_estado = self.create_metric_box(self.metrics_container, "Estado de Vía", "DESPEJADA", "#facc15")
        self.lbl_tendencia = self.create_metric_box(self.metrics_container, "Tendencia", "ESTABLE", "#c084fc")
        self.lbl_alertas = self.create_metric_box(self.metrics_container, "Nivel de Riesgo", "BAJO", "#34d399")
        
        # Consola de Reportes (Log Automático en Interfaz)
        console_frame = ctk.CTkFrame(self.right_panel, fg_color="#1f2937", corner_radius=8)
        console_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Header de Consola
        header_consola = ctk.CTkFrame(console_frame, fg_color="transparent")
        header_consola.pack(fill="x", padx=10, pady=(5,0))
        ctk.CTkLabel(header_consola, text="Consola de Reportes", font=("Inter", 12, "bold")).pack(side="left")
        
        # Selector de tiempo para log automático
        self.auto_log_interval = tk.IntVar(value=0)
        opt_menu = ctk.CTkOptionMenu(header_consola, variable=self.auto_log_interval, 
                                     values=["0", "5", "10", "30", "60"], width=60, height=20, font=("Inter", 10))
        opt_menu.pack(side="right")
        ctk.CTkLabel(header_consola, text="Frecuencia (s):", font=("Inter", 10)).pack(side="right", padx=5)

        # Caja de texto para log
        self.log_textbox = ctk.CTkTextbox(console_frame, fg_color="#111827", text_color="#34d399", font=("Courier", 11))
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_textbox.insert("0.0", "--- Historial de Métricas ---\n")
        self.log_textbox.configure(state="disabled")

        # Controles
        controls_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=5)

        # Fila 1: Play / Pause / Cambiar
        btn_row1 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_row1.pack(fill="x", pady=5)
        self.btn_play = ctk.CTkButton(btn_row1, text="▶ Iniciar", width=100, fg_color="#047857", hover_color="#065f46", command=self.play)
        self.btn_play.pack(side="left", padx=5)
        self.btn_pause = ctk.CTkButton(btn_row1, text="⏸ Pausa", width=100, fg_color="#b45309", hover_color="#92400e", command=self.pause)
        self.btn_pause.pack(side="left", padx=5)
        ctk.CTkButton(btn_row1, text="📁 Video", width=100, fg_color="#1d4ed8", hover_color="#1e3a8a", command=self.change_video).pack(side="right", padx=5)

        # Separador
        ctk.CTkFrame(self.right_panel, height=2, fg_color="#374151").pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.right_panel, text="EXPORTACIÓN / REPORTES", font=("Inter", 12, "bold"), text_color="#9ca3af").pack()

        # Botones JSON
        btn_row_json = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        btn_row_json.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_row_json, text="📄 JSON (Instante)", fg_color="#4b5563", hover_color="#374151", command=self.export_json_instante).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_row_json, text="📄 JSON (Historial)", fg_color="#4b5563", hover_color="#374151", command=self.export_json_historial).pack(side="right", fill="x", expand=True, padx=5)
        
        # Botones Huffman
        btn_row_huff = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        btn_row_huff.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_row_huff, text="🗜️ Huffman (Instante)", fg_color="#7e22ce", hover_color="#6b21a8", command=self.export_huffman_instante).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_row_huff, text="🗜️ Huffman (Historial)", fg_color="#7e22ce", hover_color="#6b21a8", command=self.export_huffman_historial).pack(side="right", fill="x", expand=True, padx=5)

        # Fila 4: Descomprimir
        ctk.CTkButton(self.right_panel, text="🔓 Descomprimir Reporte Binario", fg_color="#0e7490", hover_color="#164e63", command=self.descomprimir).pack(fill="x", padx=25, pady=5)

    def create_metric_box(self, parent, title, initial_val, color):
        frame = ctk.CTkFrame(parent, fg_color="#1f2937", corner_radius=8)
        frame.pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text=title, font=("Inter", 12), text_color="#9ca3af").pack(side="left", padx=15, pady=8)
        val_lbl = ctk.CTkLabel(frame, text=initial_val, font=("Inter", 14, "bold"), text_color=color)
        val_lbl.pack(side="right", padx=15, pady=8)
        return val_lbl

    def load_engine(self, path):
        if self.engine:
            self.engine.release()
        self.engine = VehicleCounterEngine(path)
        self.historial_flujo.clear()
        self.tiempo_historial.clear()
        self.historial_completo.clear()
        self.start_time = time.time()
        self.last_log_time = time.time()
        self.last_historial_time = time.time()

    def play(self):
        self.running = True

    def pause(self):
        self.running = False

    def change_video(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos MP4", "*.mp4"), ("Todos", "*.*")])
        if path:
            self.running = False
            self.load_engine(path)
            self.video_label.configure(image="")
            self.lbl_vehiculos.configure(text="0")
            self.lbl_flujo.configure(text="0.0")

    def export_json_instante(self):
        if self.engine and self.engine.last_metrics:
            nombre = export_summary_json(self.engine.last_metrics, is_history=False)
            if nombre:
                messagebox.showinfo("Exportación", f"JSON del momento guardado como:\n{nombre}")

    def export_json_historial(self):
        if self.historial_completo:
            nombre = export_summary_json(self.historial_completo, is_history=True)
            if nombre:
                messagebox.showinfo("Exportación", f"Historial JSON guardado como:\n{nombre}")
        else:
            messagebox.showwarning("Atención", "No hay datos en el historial aún.")

    def export_huffman_instante(self):
        if self.engine and self.engine.last_metrics:
            bin_name, dict_name = export_summary_json_huffman(self.engine.last_metrics, is_history=False)
            if bin_name:
                messagebox.showinfo("Huffman", f"Instante comprimido:\n{bin_name}\n{dict_name}")

    def export_huffman_historial(self):
        if self.historial_completo:
            bin_name, dict_name = export_summary_json_huffman(self.historial_completo, is_history=True)
            if bin_name:
                messagebox.showinfo("Huffman", f"Historial comprimido:\n{bin_name}\n{dict_name}")
        else:
            messagebox.showwarning("Atención", "No hay datos en el historial aún.")

    def descomprimir(self):
        ruta_bin = filedialog.askopenfilename(title="Selecciona el archivo binario (.bin)", filetypes=[("Archivos BIN", "*.bin")])
        if not ruta_bin: return
        
        ruta_dict = filedialog.askopenfilename(title="Selecciona el diccionario (.json)", filetypes=[("Archivos JSON", "*.json")])
        if not ruta_dict: return
        
        ruta_bin = Path(ruta_bin)
        ruta_dict = Path(ruta_dict)
        
        if not ruta_bin.exists() or not ruta_dict.exists():
            messagebox.showerror("Error", "No se encontraron los archivos binario/diccionario en data/json.")
            return
            
        try:
            datos = descompresor_huffman(ruta_bin, ruta_dict)
            json_str = json.dumps(datos, indent=4, ensure_ascii=False)
            
            # Crear ventana para mostrar resultado
            top = ctk.CTkToplevel(self)
            top.title("Datos Recuperados (Huffman)")
            top.geometry("500x400")
            top.attributes("-topmost", True)
            
            # Tamaño info
            size_orig = len(json.dumps(datos, ensure_ascii=False).encode('utf-8'))
            size_comp = ruta_bin.stat().st_size
            ahorro = 100 - ((size_comp / size_orig) * 100) if size_orig > 0 else 0
            
            info = ctk.CTkLabel(top, text=f"Tamaño Original: {size_orig} bytes | Comprimido: {size_comp} bytes\nAhorro: {ahorro:.1f}%", font=("Inter", 12, "bold"), text_color="#00d4ff")
            info.pack(pady=10)
            
            txt = ctk.CTkTextbox(top, width=460, height=300, fg_color="#1f2937", text_color="#34d399")
            txt.pack(pady=10)
            txt.insert("0.0", json_str)
            txt.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error de Descompresión", str(e))

    def update_metrics_ui(self, metrics):
        if not metrics: return
        
        self.lbl_aforo.configure(text=str(metrics.get("total_count", 0)))
        self.lbl_vehiculos.configure(text=str(metrics.get("total_vehicles", 0)))
        flujo = metrics.get("flujo_por_minuto", 0.0)
        self.lbl_flujo.configure(text=f"{flujo:.1f}")
        
        estado = metrics.get("fluidez_avance", "DESPEJADA")
        color_est = "#facc15"
        if "LIBRE" in estado or "DESPEJADA" in estado: color_est = "#34d399"
        elif "SEVERA" in estado: color_est = "#ef4444"
        self.lbl_estado.configure(text=estado, text_color=color_est)
        
        tendencia = metrics.get("tendencia", "ESTABLE")
        color_tend = "#c084fc"
        if tendencia == "AUMENTANDO": color_tend = "#ef4444"
        elif tendencia == "DISMINUYENDO": color_tend = "#34d399"
        self.lbl_tendencia.configure(text=tendencia, text_color=color_tend)
        
        alerta = metrics.get("alerta_embotellamiento", False)
        if alerta:
            self.lbl_alertas.configure(text="¡ALTO (Embotellamiento)!", text_color="#ef4444")
        else:
            clusters = metrics.get("cluster_metrics", [])
            riesgos = [c["riesgo"] for c in clusters]
            if "MEDIO" in riesgos:
                self.lbl_alertas.configure(text="PRECAUCIÓN", text_color="#facc15")
            else:
                self.lbl_alertas.configure(text="NORMAL", text_color="#34d399")

        # Gráfica
        t_actual = time.time() - self.start_time
        self.tiempo_historial.append(t_actual)
        self.historial_flujo.append(flujo)
        
        if len(self.historial_flujo) > 100:
            self.tiempo_historial.pop(0)
            self.historial_flujo.pop(0)
            
        self.line.set_data(self.tiempo_historial, self.historial_flujo)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def handle_auto_log(self, metrics):
        intervalo = self.auto_log_interval.get()
        if intervalo > 0 and metrics:
            now = time.time()
            if now - self.last_log_time >= intervalo:
                # Escribir en la consola de la interfaz en lugar de guardar en disco
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                
                log_data = {
                    "tiempo": timestamp,
                    "flujo_min": metrics.get("flujo_por_minuto", 0.0),
                    "estado": metrics.get("fluidez_avance", "N/A"),
                    "riesgo": "ALTO" if metrics.get("alerta_embotellamiento") else "NORMAL",
                    "vehiculos_actuales": metrics.get("total_vehicles", 0)
                }
                
                log_str = json.dumps(log_data, ensure_ascii=False)
                
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", f"[{timestamp}] {log_str}\n")
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")
                
                self.last_log_time = now

    def update_loop(self):
        if self.running and self.engine:
            frame_cv, dashboard_cv, metrics = self.engine.tick()
            
            if frame_cv is not None:
                # Mostrar frame en Tkinter
                frame_rgb = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                
            if metrics:
                self.update_metrics_ui(metrics)
                self.handle_auto_log(metrics)
                
                # Guardar el historial en memoria cada 1 segundo exacto
                now = time.time()
                if now - getattr(self, 'last_historial_time', 0) >= 1.0:
                    import datetime
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    registro = {
                        "tiempo": ts,
                        "aforo_acumulado": metrics.get("total_count", 0),
                        "flujo_min": metrics.get("flujo_por_minuto", 0.0),
                        "estado": metrics.get("fluidez_avance", "N/A"),
                        "riesgo": "ALTO" if metrics.get("alerta_embotellamiento") else "NORMAL",
                        "vehiculos_actuales": metrics.get("total_vehicles", 0)
                    }
                    self.historial_completo.append(registro)
                    self.last_historial_time = now

        # Llamar a sí misma en ~30ms (equivale a ~33 fps si el procesamiento es rápido)
        self.after(30, self.update_loop)
