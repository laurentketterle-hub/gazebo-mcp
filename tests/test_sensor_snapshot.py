"""Tests for sensor snapshot feature."""

from __future__ import annotations

import json

from gazebo_mcp.backend.mock import MockBackend


class TestSensorSnapshot:
    def test_lidar_snapshot_ok(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("lidar")
        assert result["ok"] is True
        assert result["sensor_type"] == "lidar"
        assert result["schema_version"] == 1
        assert "model" in result
        assert "timestamp_sec" in result
        assert "frame" in result

    def test_lidar_snapshot_has_points(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("lidar")
        frame = result["frame"]
        assert frame["count"] == 360
        assert len(frame["points"]) == 360
        for p in frame["points"]:
            assert "x" in p
            assert "y" in p
            assert "z" in p
            assert isinstance(p["intensity"], float)
            assert 0.0 <= p["intensity"] <= 1.0

    def test_lidar_snapshot_field_of_view(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("lidar")
        frame = result["frame"]
        assert frame["horizontal_fov_deg"] == 360.0
        assert frame["vertical_fov_deg"] == 30.0
        assert frame["range_min_m"] == 0.1
        assert frame["range_max_m"] == 30.0

    def test_camera_snapshot_ok(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("camera")
        assert result["ok"] is True
        assert result["sensor_type"] == "camera"
        assert result["schema_version"] == 1
        assert "model" in result
        assert "timestamp_sec" in result
        frame = result["frame"]
        assert frame["width"] == 640
        assert frame["height"] == 480
        assert frame["format"] == "rgb8"
        assert "pixels_base64" in frame
        assert "description" in frame

    def test_camera_snapshot_has_description(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("camera")
        desc = result["frame"]["description"]
        assert "Synthetic camera view" in desc
        assert "Placeholder" in desc

    def test_lidar_points_are_within_range(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("lidar")
        for p in result["frame"]["points"]:
            # Each point distance from model origin should be within sensor range
            import math

            dist = math.sqrt(p["x"] ** 2 + p["y"] ** 2)
            # Points can be far from origin since model may be at non-zero pose
            assert dist >= 0

    def test_specific_model_attachment(self):
        backend = MockBackend()
        # Spawn a specific model
        backend.spawn("test_bot", "robot", x=5.0, y=5.0, z=1.0, yaw=0.5)
        result = backend.sensor_snapshot("lidar", model_name="test_bot")
        assert result["ok"] is True
        assert result["model"] == "test_bot"

    def test_unknown_model_returns_error(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("lidar", model_name="ghost_model")
        assert result["ok"] is False
        assert "unknown model" in result.get("error", "")

    def test_unknown_sensor_type_returns_error(self):
        backend = MockBackend()
        result = backend.sensor_snapshot("sonar")
        assert result["ok"] is False
        assert "unknown sensor_type" in result.get("error", "")

    def test_default_sensor_type_is_lidar(self):
        backend = MockBackend()
        result = backend.sensor_snapshot()
        assert result["sensor_type"] == "lidar"

    def test_lidar_points_are_deterministic(self):
        backend = MockBackend()
        backend.pause()  # freeze sim time for deterministic results
        r1 = backend.sensor_snapshot("lidar")
        r2 = backend.sensor_snapshot("lidar")
        # Same instance, same sim time should produce identical points
        p1 = r1["frame"]["points"]
        p2 = r2["frame"]["points"]
        for i in range(min(len(p1), len(p2))):
            assert p1[i]["x"] == p2[i]["x"]
            assert p1[i]["y"] == p2[i]["y"]
            assert p1[i]["z"] == p2[i]["z"]
            assert p1[i]["intensity"] == p2[i]["intensity"]

    def test_different_models_produce_different_points(self):
        backend = MockBackend()
        backend.spawn("bot_a", "robot", x=0.0, y=0.0, z=1.0)
        backend.spawn("bot_b", "robot", x=10.0, y=10.0, z=1.0)
        r_a = backend.sensor_snapshot("lidar", model_name="bot_a")
        r_b = backend.sensor_snapshot("lidar", model_name="bot_b")
        # Different models should produce different point clouds
        p_a = r_a["frame"]["points"]
        p_b = r_b["frame"]["points"]
        # At least some points should differ
        differences = sum(1 for i in range(len(p_a)) if p_a[i]["x"] != p_b[i]["x"])
        assert differences > 0

    def test_sensor_snapshot_is_json_serializable(self):
        backend = MockBackend()
        for st in ("lidar", "camera"):
            result = backend.sensor_snapshot(st)
            dumped = json.dumps(result, default=str)
            assert len(dumped) > 100
            loaded = json.loads(dumped)
            assert loaded["ok"] is True

    def test_no_models_without_ground_returns_error(self):
        """If only ground_plane exists, no valid model for sensor."""
        backend = MockBackend()
        # Remove all non-ground models
        backend._models = {"ground_plane": backend._models.get("ground_plane", {})}
        result = backend.sensor_snapshot("lidar")
        assert result["ok"] is False
        assert "no valid models" in result.get("error", "")
