"""GUI-style frame renderer for the headless demo.

The desktop app (CustomTkinter) cannot be recorded without a display, so this
module redraws the same layout with OpenCV: video area, live flow chart and the
metrics panel on the right.

Only ``cv2`` and ``numpy`` are used here so the gallery script can import the
layout constants without pulling the heavy vision dependencies.
"""

import cv2
import numpy as np

# Canvas and layout geometry (native resolution, scaled later if needed)
CANVAS_W = 1600
CANVAS_H = 900

LEFT_X1, LEFT_X2 = 32, 1112
RIGHT_X1, RIGHT_X2 = 1136, 1568
TOP, BOTTOM = 24, 868

VIDEO_BOTTOM = 606
CHART_TOP = 626

# Palette (BGR)
COLOR_BG = (25, 15, 11)          # #0b0f19
COLOR_PANEL = (39, 24, 17)       # #111827
COLOR_BOX = (42, 23, 15)         # #0f172a
COLOR_BORDER = (58, 47, 39)      # #2b2f3a-ish
COLOR_TEXT = (235, 235, 235)
COLOR_MUTED = (156, 163, 175)
COLOR_CYAN = (255, 212, 0)       # #00d4ff
COLOR_GREEN = (153, 211, 52)     # #34d399
COLOR_YELLOW = (21, 204, 250)    # #facc15
COLOR_PURPLE = (252, 132, 192)   # #c084fc
COLOR_RED = (68, 68, 239)        # #ef4444
COLOR_CHART = (55, 41, 31)       # #1f2937


def _text(img, text, x, y, scale=0.5, color=COLOR_TEXT, thickness=1,
          align="left"):
    text = str(text)
    (w, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    cv2.putText(img, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness, cv2.LINE_AA)


def _fit_scale(text, max_width, start=0.55, thickness=2):
    scale = start
    while scale > 0.3:
        (w, _), _ = cv2.getTextSize(str(text), cv2.FONT_HERSHEY_SIMPLEX,
                                    scale, thickness)
        if w <= max_width:
            return scale
        scale -= 0.02
    return scale


def _rounded_rect(img, x1, y1, x2, y2, color, radius=12, thickness=-1):
    radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    for cx, cy in ((x1 + radius, y1 + radius), (x2 - radius, y1 + radius),
                   (x1 + radius, y2 - radius), (x2 - radius, y2 - radius)):
        cv2.circle(img, (cx, cy), radius, color, thickness)


def _fit_inside(img, box_w, box_h):
    height, width = img.shape[:2]
    scale = min(box_w / width, box_h / height)
    return cv2.resize(img, (max(1, int(width * scale)),
                            max(1, int(height * scale))),
                      interpolation=cv2.INTER_AREA)


def _draw_video(canvas, video_frame):
    box_w = LEFT_X2 - LEFT_X1
    box_h = VIDEO_BOTTOM - TOP
    cv2.rectangle(canvas, (LEFT_X1, TOP), (LEFT_X2, VIDEO_BOTTOM), (8, 8, 8), -1)

    fitted = _fit_inside(video_frame, box_w, box_h)
    fh, fw = fitted.shape[:2]
    x = LEFT_X1 + (box_w - fw) // 2
    y = TOP + (box_h - fh) // 2
    canvas[y:y + fh, x:x + fw] = fitted
    cv2.rectangle(canvas, (LEFT_X1, TOP), (LEFT_X2, VIDEO_BOTTOM), COLOR_BORDER, 1)


def _draw_chart(canvas, flow_history):
    x1, x2 = LEFT_X1, LEFT_X2
    y1, y2 = CHART_TOP, BOTTOM
    _rounded_rect(canvas, x1, y1, x2, y2, COLOR_CHART, radius=16)
    _text(canvas, "Live Vehicle Flow (vehs/min)", (x1 + x2) // 2, y1 + 34,
          scale=0.6, color=COLOR_CYAN, align="center")

    px1, px2 = x1 + 150, x2 - 40
    py1, py2 = y1 + 55, y2 - 40

    values = list(flow_history)[-100:]
    peak = max([0.0] + values)
    top_value = max(1.0, peak * 1.25)

    for i in range(5):
        gy = int(py1 + (py2 - py1) * i / 4)
        cv2.line(canvas, (px1, gy), (px2, gy), (70, 58, 48), 1, cv2.LINE_AA)
        label = top_value * (1 - i / 4)
        _text(canvas, f"{label:.1f}", px1 - 12, gy + 5, scale=0.42,
              color=COLOR_MUTED, align="right")

    cv2.line(canvas, (px1, py2), (px2, py2), COLOR_MUTED, 1, cv2.LINE_AA)
    cv2.line(canvas, (px1, py1), (px1, py2), COLOR_MUTED, 1, cv2.LINE_AA)

    if values:
        count = max(1, len(values) - 1)
        points = []
        for i, value in enumerate(values):
            px = int(px1 + (px2 - px1) * i / count)
            py = int(py2 - (py2 - py1) * min(value / top_value, 1.0))
            points.append((px, py))
        if len(points) > 1:
            cv2.polylines(canvas, [np.array(points, dtype=np.int32)], False,
                          COLOR_GREEN, 2, cv2.LINE_AA)
        cv2.circle(canvas, points[-1], 4, COLOR_GREEN, -1, cv2.LINE_AA)

    _text(canvas, "time", px2, py2 + 28, scale=0.4, color=COLOR_MUTED,
          align="right")


def _metric_value(metrics):
    state = metrics.get("flow_state", "CLEAR")
    state_color = COLOR_YELLOW
    if "FREE" in state or "CLEAR" in state:
        state_color = COLOR_GREEN
    elif "SEVERE" in state:
        state_color = COLOR_RED

    trend = metrics.get("trend", "STABLE")
    trend_color = COLOR_PURPLE
    if trend == "INCREASING":
        trend_color = COLOR_RED
    elif trend == "DECREASING":
        trend_color = COLOR_GREEN

    if metrics.get("congestion_alert"):
        risk_text, risk_color = "HIGH (Traffic Jam)!", COLOR_RED
    else:
        risks = [c.get("risk") for c in metrics.get("cluster_metrics", [])]
        if "MEDIUM" in risks:
            risk_text, risk_color = "CAUTION", COLOR_YELLOW
        else:
            risk_text, risk_color = "NORMAL", COLOR_GREEN

    return [
        ("Total Count", str(metrics.get("total_count", 0)), COLOR_GREEN),
        ("Vehicles in Scene", str(metrics.get("total_vehicles", 0)), COLOR_CYAN),
        ("Flow (vehs/min)", f"{metrics.get('flow_per_minute', 0.0):.1f}",
         COLOR_CYAN),
        ("Road State", state, state_color),
        ("Trend", trend, trend_color),
        ("Risk Level", risk_text, risk_color),
    ]


def _draw_panel(canvas, metrics, console_lines):
    _rounded_rect(canvas, RIGHT_X1, TOP, RIGHT_X2, BOTTOM, COLOR_PANEL,
                  radius=16)
    center = (RIGHT_X1 + RIGHT_X2) // 2

    _text(canvas, "TRAFFIC MONITOR", center, TOP + 52, scale=0.85,
          color=COLOR_CYAN, thickness=2, align="center")
    _text(canvas, "INTELLIGENT COUNTING SYSTEM", center, TOP + 82,
          scale=0.42, color=COLOR_MUTED, align="center")

    box_x1, box_x2 = RIGHT_X1 + 20, RIGHT_X2 - 20
    y = TOP + 116
    box_h, gap = 56, 10

    for label, value, color in _metric_value(metrics):
        _rounded_rect(canvas, box_x1, y, box_x2, y + box_h, COLOR_BOX,
                      radius=10)
        _rounded_rect(canvas, box_x1, y, box_x2, y + box_h, COLOR_BORDER,
                      radius=10, thickness=1)
        _text(canvas, label, box_x1 + 16, y + box_h // 2 + 7, scale=0.5,
              color=COLOR_MUTED)
        scale = _fit_scale(value, box_x2 - box_x1 - 190, start=0.55)
        _text(canvas, value, box_x2 - 16, y + box_h // 2 + 8, scale=scale,
              color=color, thickness=2, align="right")
        y += box_h + gap

    _text(canvas, "Report Console", box_x1, y + 26, scale=0.5,
          color=COLOR_TEXT)
    _text(canvas, "Frequency (s):", box_x2 - 70, y + 26, scale=0.4,
          color=COLOR_MUTED, align="right")
    _rounded_rect(canvas, box_x2 - 60, y + 6, box_x2, y + 38, COLOR_BOX,
                  radius=6)
    _text(canvas, "0", box_x2 - 30, y + 29, scale=0.45, color=COLOR_TEXT,
          align="center")

    console_y1 = y + 50
    console_y2 = BOTTOM - 78
    _rounded_rect(canvas, box_x1, console_y1, box_x2, console_y2, COLOR_BOX,
                  radius=10)
    _rounded_rect(canvas, box_x1, console_y1, box_x2, console_y2, COLOR_BORDER,
                  radius=10, thickness=1)

    lines = ["--- Metrics History ---"] + list(console_lines)[-6:]
    line_y = console_y1 + 28
    for line in lines:
        _text(canvas, line, box_x1 + 14, line_y, scale=0.4, color=COLOR_GREEN)
        line_y += 24
        if line_y > console_y2 - 10:
            break

    button_y1 = BOTTOM - 58
    button_y2 = BOTTOM - 18
    buttons = [
        (box_x1, box_x1 + 108, (90, 160, 45), "Start"),
        (box_x1 + 118, box_x1 + 236, (30, 110, 210), "Pause"),
        (box_x2 - 108, box_x2, (190, 110, 25), "Video"),
    ]
    for bx1, bx2, color, label in buttons:
        _rounded_rect(canvas, bx1, button_y1, bx2, button_y2, color, radius=8)
        _text(canvas, label, (bx1 + bx2) // 2, button_y1 + 27, scale=0.45,
              color=(255, 255, 255), align="center")


def render_gui_frame(video_frame, metrics, flow_history, console_lines=None):
    """Return a frame laid out like the CustomTkinter app."""
    metrics = metrics or {}
    canvas = np.full((CANVAS_H, CANVAS_W, 3), COLOR_BG, dtype=np.uint8)

    _draw_video(canvas, video_frame)
    _draw_chart(canvas, flow_history or [])
    _draw_panel(canvas, metrics, console_lines or [])

    return canvas


# Kept for the gallery script: right panel crop at native resolution.
def panel_crop(frame):
    height, width = frame.shape[:2]
    x1 = int(RIGHT_X1 * width / CANVAS_W)
    x2 = int(RIGHT_X2 * width / CANVAS_W)
    return frame[:, x1:x2]
