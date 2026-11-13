from src.analytics.clustering import detect_traffic_clusters
from src.analytics.graphs import build_proximity_graph


def test_proximity_graph_connects_only_close_vehicles():
    detections = [
        {"id": 1, "center": (100, 100)},
        {"id": 2, "center": (110, 100)},
        {"id": 3, "center": (900, 100)},
    ]

    graph = build_proximity_graph(detections, (720, 1280), distance_factor=0.05)

    # 5% of 1280 = 64 px: vehicles 1 and 2 are neighbors, vehicle 3 is far away.
    assert 2 in graph[1]
    assert 1 in graph[2]
    assert graph[3] == []


def test_detect_clusters_empty_input():
    assert detect_traffic_clusters([], (720, 1280)) == {}
