from src.analytics.metrics import calculate_metrics


def _state(total_count=0):
    return {
        "crossing_timestamps": [],
        "metrics_history": [],
        "total_count": total_count,
    }


def test_empty_scene_is_clear_road():
    metrics = calculate_metrics([], {}, {}, (720, 1280), _state())

    assert metrics["total_vehicles"] == 0
    assert metrics["flow_state"] == "CLEAR ROAD"
    assert metrics["flow_per_minute"] == 0.0
    assert metrics["cluster_metrics"] == []
    assert metrics["congestion_alert"] is False


def test_metrics_expose_expected_schema():
    metrics = calculate_metrics([], {}, {}, (720, 1280), _state(total_count=5))

    expected_keys = {
        "total_vehicles",
        "active_cluster_count",
        "spatial_interaction_pct",
        "flow_level",
        "flow_state",
        "flow_per_minute",
        "total_count",
        "trend",
        "prev_ids_pos",
        "cluster_metrics",
        "congestion_alert",
    }
    assert expected_keys.issubset(metrics.keys())
    assert metrics["total_count"] == 5
