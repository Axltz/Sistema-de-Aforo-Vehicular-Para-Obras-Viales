import cv2
import numpy as np


def draw_overlay(frame, detections, analysis_result):
    height, width = frame.shape[:2]
    dashboard = np.zeros((700, 400, 3), dtype=np.uint8) + 30
    metrics = analysis_result["metrics"]

    def dashboard_text(target, text, x, y, color=(255, 255, 255), scale=0.6, thickness=1):
        cv2.putText(target, str(text), (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

    # HEADER
    cv2.rectangle(dashboard, (0, 0), (400, 60), (50, 50, 50), -1)
    dashboard_text(dashboard, "PROFESSIONAL TRAFFIC MONITOR", 20, 40, (0, 255, 255), 0.7, 2)

    y_pos = 100
    # SECTION 1: COUNT AND FLOW
    dashboard_text(dashboard, "FLOW STATISTICS", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    dashboard_text(dashboard, f"Vehicles on screen: {metrics.get('total_vehicles', 0)}", 20, y_pos, (255, 255, 255), 0.6, 1); y_pos += 30
    dashboard_text(dashboard, f"Vehicles that crossed: {metrics['total_count']}", 20, y_pos, (0, 255, 0), 0.6, 2); y_pos += 30
    dashboard_text(dashboard, f"Current rate: {metrics.get('flow_per_minute', 0)} vehs/min", 20, y_pos, (255, 255, 0), 0.6, 2); y_pos += 50

    # SECTION 2: ROAD DIAGNOSIS
    dashboard_text(dashboard, "OVERALL TRAFFIC STATE", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30
    dashboard_text(dashboard, f"{metrics['flow_state']}", 20, y_pos, (255, 255, 255), 0.65, 2); y_pos += 30
    dashboard_text(dashboard, f"Behavior: {metrics['flow_level']}", 20, y_pos, (150, 150, 150), 0.5, 1); y_pos += 50

    # SECTION 3: ROAD EVENTS (Clusters and Congestion)
    dashboard_text(dashboard, "EVENTS AND CLUSTERS MONITOR", 20, y_pos, (200, 200, 200), 0.5); y_pos += 30

    if metrics.get("congestion_alert"):
        # Blinking visual alert
        alert_color = (0, 0, 255) if int(cv2.getTickCount() / cv2.getTickFrequency() * 2) % 2 == 0 else (0, 100, 255)
        cv2.rectangle(dashboard, (10, y_pos - 20), (390, y_pos + 10), alert_color, -1)
        dashboard_text(dashboard, "TRAFFIC JAM DETECTED!", 60, y_pos, (255, 255, 255), 0.6, 2)
    y_pos += 30

    cluster_metrics = metrics.get("cluster_metrics", [])
    if not cluster_metrics:
        dashboard_text(dashboard, "No risk clusters.", 20, y_pos, (0, 255, 0), 0.5); y_pos += 25
    else:
        for i, cluster_data in enumerate(cluster_metrics):
            cluster_name = cluster_data["name"]
            cluster_color = [(255, 100, 0), (0, 150, 255), (100, 0, 255), (0, 255, 150)][i % 4]
            # Format: "Vehicle Group: 4 vehs - Moving"
            status_text = "Stopped (HIGH risk)" if cluster_data['risk'] == "HIGH" else "Moving"
            dashboard_text(dashboard, f"{cluster_name}: {cluster_data['count']} vehs - {status_text}", 20, y_pos, cluster_color, 0.45, 1); y_pos += 25

    # SYSTEM CONTROLS (footer)
    cv2.putText(dashboard, "CONTROLS:", (20, 640), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
    cv2.putText(dashboard, "[E] Export JSON", (20, 665), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 1)
    cv2.putText(dashboard, "[Q] Quit System", (20, 685), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)

    # MAIN VIDEO VISUALS (Counting Line - Neon Laser Design)
    counting_line = analysis_result["line"]
    if counting_line and counting_line["start"] != (0, 0):
        p1, p2 = counting_line["start"], counting_line["end"]
        # Layer 1: Outer glow (Neon Magenta)
        cv2.line(frame, p1, p2, (180, 0, 255), 6, cv2.LINE_AA)
        # Layer 2: Inner glow (Electric Cyan)
        cv2.line(frame, p1, p2, (255, 255, 0), 3, cv2.LINE_AA)
        # Layer 3: Bright core (Pure White)
        cv2.line(frame, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

        # Floating aesthetic "military HUD" label
        line_label = "ACTIVE COUNTING ZONE"
        (w, h), _ = cv2.getTextSize(line_label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        lx, ly = p1[0] + 15, p1[1] - 10
        cv2.rectangle(frame, (lx - 4, ly + 4), (lx + w + 4, ly - h - 4), (20, 20, 20), -1)
        cv2.rectangle(frame, (lx - 4, ly + 4), (lx + w + 4, ly - h - 4), (255, 255, 0), 1)
        cv2.putText(frame, line_label, (lx, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

    # Quick lookup of the (X, Y) of any vehicle by its ID
    center_positions = {v["id"]: v["center"] for v in detections}

    # 2. Draw congestion zones
    vehicles_at_risk = set()

    for i, cluster_data in enumerate(cluster_metrics):
        cluster_name = cluster_data["name"]
        vehicle_ids = cluster_data["ids"]
        risk = cluster_data["risk"]

        if risk == "HIGH":
            vehicles_at_risk.update(vehicle_ids)

        cluster_points = [center_positions[vid] for vid in vehicle_ids if vid in center_positions]
        if cluster_points:
            cx = int(np.mean([p[0] for p in cluster_points]))
            cy = int(np.min([p[1] for p in cluster_points])) - 20
            text_color = (0, 0, 255) if risk == "HIGH" else (255, 150, 0)

            # Draw the cluster's floating label
            (w, h), _ = cv2.getTextSize(cluster_name, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (cx - 44, cy + 4), (cx - 44 + w + 8, cy - h - 4), (20, 20, 20), -1)
            cv2.rectangle(frame, (cx - 44, cy + 4), (cx - 44 + w + 8, cy - h - 4), text_color, 1)
            cv2.putText(frame, cluster_name, (cx - 40, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # 3. Draw individual vehicles (Cyberpunk HUD)
    for v in detections:
        vid = v["id"]
        cx, cy = v["center"]

        # Format the ID aesthetically as "#01", "#02", etc.
        tag_id = f"#{vid:02d}"

        if vid in vehicles_at_risk:
            # JAMMED VEHICLE: Danger design (Neon Orange/Red with pulses)
            # Outer alert ring
            cv2.circle(frame, (cx, cy), 11, (0, 80, 255), 2, cv2.LINE_AA)
            # Blinking outer ring
            cv2.circle(frame, (cx, cy), 14, (0, 0, 255), 1, cv2.LINE_AA)
            # Bright center
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1, cv2.LINE_AA)

            # Floating red ID label with dark high-contrast background
            (w, h), _ = cv2.getTextSize(tag_id, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.rectangle(frame, (cx - 15, cy - 20), (cx - 15 + w + 6, cy - 20 - h - 4), (10, 10, 60), -1)
            cv2.rectangle(frame, (cx - 15, cy - 20), (cx - 15 + w + 6, cy - 20 - h - 4), (0, 0, 255), 1)
            cv2.putText(frame, tag_id, (cx - 12, cy - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
        else:
            # NORMAL VEHICLE: Premium free-flow design (Electric Cyan / White)
            # Thin outer ring
            cv2.circle(frame, (cx, cy), 7, (255, 255, 0), 2, cv2.LINE_AA)
            # Bright white center
            cv2.circle(frame, (cx, cy), 3, (255, 255, 255), -1, cv2.LINE_AA)

            # Floating cyan ID label with dark high-contrast background
            (w, h), _ = cv2.getTextSize(tag_id, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            cv2.rectangle(frame, (cx - 15, cy - 16), (cx - 15 + w + 6, cy - 16 - h - 4), (15, 15, 15), -1)
            cv2.rectangle(frame, (cx - 15, cy - 16), (cx - 15 + w + 6, cy - 16 - h - 4), (255, 255, 0), 1)
            cv2.putText(frame, tag_id, (cx - 12, cy - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)

    return frame, dashboard
