import cv2
import time
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk

# Matplotlib for the real-time graph embedded in Tkinter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.config import DEFAULT_VIDEO_PATH, FRAME_SKIP_FACTOR
from src.detection.detection import frame_detection
from src.pipeline.pipeline import process_frame
from src.analytics.processing import create_system_state, count_vehicles, calibrate_system, export_summary_json_huffman
from src.storage.json_writer import export_summary_json
from src.visualization.overlay import draw_overlay
from src.analytics.huffman import decompress_huffman
import json


class VehicleCounterEngine:
    """Encapsulates the logic loop without breaking OpenCV's continuous state."""
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
        # The state is NOT reset to keep the short-term vehicle memory (optional,
        # although if it is a different video, the ideal is to clear the state).
        # To avoid weird cross-video interference, we do recreate the state when
        # changing files, but we keep the same engine if only restarting.
        if new_path:
            self.state = create_system_state()
        else:
            # If it is the same video repeating, we keep the history so it does
            # not take a sudden jump.
            pass
        self.frame_count = 0
        self.result = None

    def release(self):
        if self.cap:
            self.cap.release()

    def tick(self):
        """Processes a single frame and returns the images and metrics.
           Original logic from main.py."""
        if not self.cap or not self.cap.isOpened():
            return None, None, self.last_metrics

        ret, frame = self.cap.read()
        if not ret:
            # Infinite loop
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return None, None, self.last_metrics

        h_orig, w_orig = frame.shape[:2]
        aspect = h_orig / w_orig
        frame = cv2.resize(frame, (1024, int(1024 * aspect)))
        self.frame_count += 1

        # STEP A: Calibration
        if not self.state["calibration_locked"]:
            if self.frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in self.state:
                raw_detections = frame_detection(frame)
                detected_vehicles = []
                for v in raw_detections:
                    vid, curr = v["id"], np.array(v["center"])
                    prev = np.array(self.state["ids_history"].get(vid, curr))
                    if self.state["orientation"] == "vertical":
                        mov = (curr[1] - prev[1]) * self.state["flow_direction"]
                    else:
                        mov = (curr[0] - prev[0]) * self.state["flow_direction"]
                    if mov >= 0:
                        detected_vehicles.append(v)
                self.state["last_detections"] = detected_vehicles
            else:
                detected_vehicles = self.state["last_detections"]

            calibrate_system(detected_vehicles, frame.shape, self.state)
            cv2.putText(frame, f"CALIBRATING FLOW... {self.state['calibration_frames']}/30", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            return frame, None, self.last_metrics

        # STEP B: Crop
        roi = self.state["active_roi"]
        cropped_frame = frame[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]

        # STEP C: Detection with skip
        yolo_ran_this_frame = (self.frame_count % FRAME_SKIP_FACTOR == 0 or "last_detections" not in self.state)
        if yolo_ran_this_frame:
            raw_detections = frame_detection(cropped_frame)
            detected_vehicles = []
            for v in raw_detections:
                vid, curr = v["id"], np.array(v["center"])
                prev = np.array(self.state["ids_history"].get(vid, curr))
                if self.state["orientation"] == "vertical":
                    mov = (curr[1] - prev[1]) * self.state["flow_direction"]
                else:
                    mov = (curr[0] - prev[0]) * self.state["flow_direction"]
                if mov >= 0:
                    detected_vehicles.append(v)
            self.state["last_detections"] = detected_vehicles
        else:
            detected_vehicles = self.state["last_detections"]

        # STEP D: Counting
        total_count, line = count_vehicles(detected_vehicles, self.state)

        # STEP E: Metrics (every 10 frames to avoid overloading)
        if self.frame_count % 10 == 0 or self.result is None:
            self.result = process_frame(detected_vehicles, cropped_frame.shape, self.state)
            self.result["metrics"]["total_count"] = total_count
            self.last_metrics = self.result["metrics"]

        # STEP F: Visual overlay (intact)
        frame_with_overlay, dashboard_img = draw_overlay(cropped_frame, detected_vehicles, self.result)

        return frame_with_overlay, dashboard_img, self.last_metrics


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Intelligent Vehicle Counting System")
        self.geometry("1400x850")
        self.configure(fg_color="#0b0f19")

        # Control variables
        self.running = False
        self.engine = None
        self.flow_history = []
        self.time_history = []
        self.full_history = []
        self.start_time = time.time()

        # Auto-log configuration
        self.auto_log_interval = tk.IntVar(value=0)  # 0 = Off
        self.last_log_time = time.time()

        self.build_ui()
        self.load_engine(DEFAULT_VIDEO_PATH)

        # Start the asynchronous loop
        self.update_loop()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=7)  # Left 70%
        self.grid_columnconfigure(1, weight=3)  # Right 30%
        self.grid_rowconfigure(0, weight=1)

        # ----------------- LEFT PANEL (VIDEO + GRAPH) -----------------
        self.left_panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.left_panel.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=7)
        self.left_panel.grid_rowconfigure(1, weight=3)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # Video label
        self.video_frame = ctk.CTkFrame(self.left_panel, fg_color="black", corner_radius=10)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.video_label = tk.Label(self.video_frame, bg="black")
        self.video_label.pack(expand=True, fill="both")

        # Matplotlib graph
        self.graph_frame = ctk.CTkFrame(self.left_panel, fg_color="#1f2937", corner_radius=10)
        self.graph_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        self.fig = Figure(figsize=(8, 2.5), dpi=100, facecolor="#1f2937")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#1f2937")
        self.ax.tick_params(colors="white")
        for spine in self.ax.spines.values():
            spine.set_color("#374151")
        self.ax.set_title("Live Vehicle Flow (vehs/min)", color="#00d4ff", fontsize=10)
        self.line, = self.ax.plot([], [], color="#00ff88", linewidth=2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both", padx=5, pady=5)

        # ----------------- RIGHT PANEL (METRICS + CONTROLS) -----------------
        self.right_panel = ctk.CTkFrame(self, fg_color="#111827", corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        # Title
        ctk.CTkLabel(self.right_panel, text="TRAFFIC MONITOR", font=("Inter", 20, "bold"), text_color="#00d4ff").pack(pady=(20, 5))
        ctk.CTkLabel(self.right_panel, text="INTELLIGENT COUNTING SYSTEM", font=("Inter", 12), text_color="#9ca3af").pack(pady=(0, 20))

        # Metric boxes
        self.metrics_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.metrics_container.pack(fill="x", padx=20, pady=5)

        self.lbl_total_count = self.create_metric_box(self.metrics_container, "Total Count", "0", "#10b981")
        self.lbl_vehicles = self.create_metric_box(self.metrics_container, "Vehicles in Scene", "0", "#00ff88")
        self.lbl_flow = self.create_metric_box(self.metrics_container, "Flow (vehs/min)", "0.0", "#00d4ff")
        self.lbl_state = self.create_metric_box(self.metrics_container, "Road State", "CLEAR", "#facc15")
        self.lbl_trend = self.create_metric_box(self.metrics_container, "Trend", "STABLE", "#c084fc")
        self.lbl_alerts = self.create_metric_box(self.metrics_container, "Risk Level", "LOW", "#34d399")

        # Report console (automatic log in the interface)
        console_frame = ctk.CTkFrame(self.right_panel, fg_color="#1f2937", corner_radius=8)
        console_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Console header
        header_console = ctk.CTkFrame(console_frame, fg_color="transparent")
        header_console.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(header_console, text="Report Console", font=("Inter", 12, "bold")).pack(side="left")

        # Time selector for the automatic log
        self.auto_log_interval = tk.IntVar(value=0)
        opt_menu = ctk.CTkOptionMenu(header_console, variable=self.auto_log_interval,
                                     values=["0", "5", "10", "30", "60"], width=60, height=20, font=("Inter", 10))
        opt_menu.pack(side="right")
        ctk.CTkLabel(header_console, text="Frequency (s):", font=("Inter", 10)).pack(side="right", padx=5)

        # Log text box
        self.log_textbox = ctk.CTkTextbox(console_frame, fg_color="#111827", text_color="#34d399", font=("Courier", 11))
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_textbox.insert("0.0", "--- Metrics History ---\n")
        self.log_textbox.configure(state="disabled")

        # Controls
        controls_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=5)

        # Row 1: Play / Pause / Change
        btn_row1 = ctk.CTkFrame(controls_frame, fg_color="transparent")
        btn_row1.pack(fill="x", pady=5)
        self.btn_play = ctk.CTkButton(btn_row1, text="▶ Start", width=100, fg_color="#047857", hover_color="#065f46", command=self.play)
        self.btn_play.pack(side="left", padx=5)
        self.btn_pause = ctk.CTkButton(btn_row1, text="⏸ Pause", width=100, fg_color="#b45309", hover_color="#92400e", command=self.pause)
        self.btn_pause.pack(side="left", padx=5)
        ctk.CTkButton(btn_row1, text="📁 Video", width=100, fg_color="#1d4ed8", hover_color="#1e3a8a", command=self.change_video).pack(side="right", padx=5)

        # Separator
        ctk.CTkFrame(self.right_panel, height=2, fg_color="#374151").pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.right_panel, text="EXPORT / REPORTS", font=("Inter", 12, "bold"), text_color="#9ca3af").pack()

        # JSON buttons
        btn_row_json = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        btn_row_json.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_row_json, text="📄 JSON (Snapshot)", fg_color="#4b5563", hover_color="#374151", command=self.export_json_snapshot).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_row_json, text="📄 JSON (History)", fg_color="#4b5563", hover_color="#374151", command=self.export_json_history).pack(side="right", fill="x", expand=True, padx=5)

        # Huffman buttons
        btn_row_huff = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        btn_row_huff.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(btn_row_huff, text="🗜️ Huffman (Snapshot)", fg_color="#7e22ce", hover_color="#6b21a8", command=self.export_huffman_snapshot).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(btn_row_huff, text="🗜️ Huffman (History)", fg_color="#7e22ce", hover_color="#6b21a8", command=self.export_huffman_history).pack(side="right", fill="x", expand=True, padx=5)

        # Row 4: Decompress
        ctk.CTkButton(self.right_panel, text="🔓 Decompress Binary Report", fg_color="#0e7490", hover_color="#164e63", command=self.decompress).pack(fill="x", padx=25, pady=5)

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
        self.flow_history.clear()
        self.time_history.clear()
        self.full_history.clear()
        self.start_time = time.time()
        self.last_log_time = time.time()
        self.last_history_time = time.time()

    def play(self):
        self.running = True

    def pause(self):
        self.running = False

    def change_video(self):
        path = filedialog.askopenfilename(filetypes=[("MP4 Files", "*.mp4"), ("All Files", "*.*")])
        if path:
            self.running = False
            self.load_engine(path)
            self.video_label.configure(image="")
            self.lbl_vehicles.configure(text="0")
            self.lbl_flow.configure(text="0.0")

    def export_json_snapshot(self):
        if self.engine and self.engine.last_metrics:
            filename = export_summary_json(self.engine.last_metrics, is_history=False)
            if filename:
                messagebox.showinfo("Export", f"Snapshot JSON saved as:\n{filename}")

    def export_json_history(self):
        if self.full_history:
            filename = export_summary_json(self.full_history, is_history=True)
            if filename:
                messagebox.showinfo("Export", f"History JSON saved as:\n{filename}")
        else:
            messagebox.showwarning("Warning", "No history data yet.")

    def export_huffman_snapshot(self):
        if self.engine and self.engine.last_metrics:
            bin_name, dict_name = export_summary_json_huffman(self.engine.last_metrics, is_history=False)
            if bin_name:
                messagebox.showinfo("Huffman", f"Compressed snapshot:\n{bin_name}\n{dict_name}")

    def export_huffman_history(self):
        if self.full_history:
            bin_name, dict_name = export_summary_json_huffman(self.full_history, is_history=True)
            if bin_name:
                messagebox.showinfo("Huffman", f"Compressed history:\n{bin_name}\n{dict_name}")
        else:
            messagebox.showwarning("Warning", "No history data yet.")

    def decompress(self):
        bin_path = filedialog.askopenfilename(title="Select the binary file (.bin)", filetypes=[("BIN Files", "*.bin")])
        if not bin_path:
            return

        dict_path = filedialog.askopenfilename(title="Select the dictionary (.json)", filetypes=[("JSON Files", "*.json")])
        if not dict_path:
            return

        bin_path = Path(bin_path)
        dict_path = Path(dict_path)

        if not bin_path.exists() or not dict_path.exists():
            messagebox.showerror("Error", "Binary/dictionary files not found in data/json.")
            return

        try:
            data = decompress_huffman(bin_path, dict_path)
            json_str = json.dumps(data, indent=4, ensure_ascii=False)

            # Create a window to show the result
            top = ctk.CTkToplevel(self)
            top.title("Recovered Data (Huffman)")
            top.geometry("500x400")
            top.attributes("-topmost", True)

            # Size info
            size_orig = len(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            size_comp = bin_path.stat().st_size
            savings = 100 - ((size_comp / size_orig) * 100) if size_orig > 0 else 0

            info = ctk.CTkLabel(top, text=f"Original Size: {size_orig} bytes | Compressed: {size_comp} bytes\nSavings: {savings:.1f}%", font=("Inter", 12, "bold"), text_color="#00d4ff")
            info.pack(pady=10)

            txt = ctk.CTkTextbox(top, width=460, height=300, fg_color="#1f2937", text_color="#34d399")
            txt.pack(pady=10)
            txt.insert("0.0", json_str)
            txt.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Decompression Error", str(e))

    def update_metrics_ui(self, metrics):
        if not metrics:
            return

        self.lbl_total_count.configure(text=str(metrics.get("total_count", 0)))
        self.lbl_vehicles.configure(text=str(metrics.get("total_vehicles", 0)))
        flow = metrics.get("flow_per_minute", 0.0)
        self.lbl_flow.configure(text=f"{flow:.1f}")

        state = metrics.get("flow_state", "CLEAR")
        state_color = "#facc15"
        if "FREE" in state or "CLEAR" in state:
            state_color = "#34d399"
        elif "SEVERE" in state:
            state_color = "#ef4444"
        self.lbl_state.configure(text=state, text_color=state_color)

        trend = metrics.get("trend", "STABLE")
        trend_color = "#c084fc"
        if trend == "INCREASING":
            trend_color = "#ef4444"
        elif trend == "DECREASING":
            trend_color = "#34d399"
        self.lbl_trend.configure(text=trend, text_color=trend_color)

        alert = metrics.get("congestion_alert", False)
        if alert:
            self.lbl_alerts.configure(text="HIGH (Traffic Jam)!", text_color="#ef4444")
        else:
            clusters = metrics.get("cluster_metrics", [])
            risks = [c["risk"] for c in clusters]
            if "MEDIUM" in risks:
                self.lbl_alerts.configure(text="CAUTION", text_color="#facc15")
            else:
                self.lbl_alerts.configure(text="NORMAL", text_color="#34d399")

        # Graph
        current_time = time.time() - self.start_time
        self.time_history.append(current_time)
        self.flow_history.append(flow)

        if len(self.flow_history) > 100:
            self.time_history.pop(0)
            self.flow_history.pop(0)

        self.line.set_data(self.time_history, self.flow_history)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def handle_auto_log(self, metrics):
        interval = self.auto_log_interval.get()
        if interval > 0 and metrics:
            now = time.time()
            if now - self.last_log_time >= interval:
                # Write to the interface console instead of saving to disk
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                log_data = {
                    "time": timestamp,
                    "flow_per_minute": metrics.get("flow_per_minute", 0.0),
                    "state": metrics.get("flow_state", "N/A"),
                    "risk": "HIGH" if metrics.get("congestion_alert") else "NORMAL",
                    "current_vehicles": metrics.get("total_vehicles", 0)
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
                # Display the frame in Tkinter
                frame_rgb = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

            if metrics:
                self.update_metrics_ui(metrics)
                self.handle_auto_log(metrics)

                # Save the in-memory history exactly every 1 second
                now = time.time()
                if now - getattr(self, 'last_history_time', 0) >= 1.0:
                    import datetime
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    record = {
                        "time": ts,
                        "accumulated_count": metrics.get("total_count", 0),
                        "flow_per_minute": metrics.get("flow_per_minute", 0.0),
                        "state": metrics.get("flow_state", "N/A"),
                        "risk": "HIGH" if metrics.get("congestion_alert") else "NORMAL",
                        "current_vehicles": metrics.get("total_vehicles", 0)
                    }
                    self.full_history.append(record)
                    self.last_history_time = now

        # Call itself in ~30ms (~33 fps equivalent if processing is fast)
        self.after(30, self.update_loop)
