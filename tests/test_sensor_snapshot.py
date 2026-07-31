"""Tests for sensor snapshot tool (gazebo-mcp #23)."""

from gazebo_mcp.backend.sensor_mock import generate_lidar_scan, generate_camera_image


class TestLidarScan:
    def test_default_scan_returns_ok(self):
        result = generate_lidar_scan()
        assert result["ok"] is True
        assert result["sensor_type"] == "lidar"
        assert result["ranges_count"] == 360
        assert len(result["ranges"]) == 360
        assert len(result["intensities"]) == 360

    def test_custom_ranges_count(self):
        result = generate_lidar_scan(ranges_count=180)
        assert result["ranges_count"] == 180
        assert len(result["ranges"]) == 180

    def test_ranges_within_bounds(self):
        result = generate_lidar_scan(max_range=10.0)
        for r in result["ranges"]:
            assert 0.1 <= r <= 10.0

    def test_intensities_in_range(self):
        result = generate_lidar_scan()
        for intensity in result["intensities"]:
            assert 0.0 <= intensity <= 1.0

    def test_no_noise_deterministic(self):
        a = generate_lidar_scan(noise=0)
        b = generate_lidar_scan(noise=0)
        assert a["ranges"] == b["ranges"]

    def test_angle_metadata(self):
        result = generate_lidar_scan(min_angle=-1.57, max_angle=1.57, ranges_count=100)
        assert result["angle_min_rad"] == -1.57
        assert result["angle_max_rad"] == 1.57
        assert result["angle_step_rad"] > 0


class TestCameraImage:
    def test_default_camera_returns_ok(self):
        result = generate_camera_image()
        assert result["ok"] is True
        assert result["sensor_type"] == "camera"
        assert result["width"] == 640
        assert result["height"] == 480
        assert result["encoding"] == "rgb8"
        assert result["channels"] == 3

    def test_custom_resolution(self):
        result = generate_camera_image(width=1920, height=1080)
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["data_size_bytes"] == 1920 * 1080 * 3

    def test_mono_encoding(self):
        result = generate_camera_image(encoding="mono8")
        assert result["channels"] == 1
        assert result["data_size_bytes"] == 640 * 480 * 1

    def test_bgr_encoding(self):
        result = generate_camera_image(encoding="bgr8")
        assert result["channels"] == 3

    def test_intrinsics_present(self):
        result = generate_camera_image()
        intrinsics = result["intrinsics"]
        assert "fx" in intrinsics
        assert "fy" in intrinsics
        assert "cx" in intrinsics
        assert "cy" in intrinsics
        assert intrinsics["distortion_model"] == "none"

    def test_pixel_stats_present(self):
        result = generate_camera_image()
        stats = result["pixel_stats"]
        assert "mean_r" in stats
        assert "mean_g" in stats
        assert "mean_b" in stats
        assert 0 <= stats["mean_r"] <= 255

    def test_deterministic(self):
        a = generate_camera_image()
        b = generate_camera_image()
        assert a["pixel_stats"] == b["pixel_stats"]


class TestSensorSchemaDoc:
    def test_schema_doc_exists(self):
        from gazebo_mcp.backend.sensor_mock import SENSOR_SCHEMA_DOC
        assert "LiDAR Scan" in SENSOR_SCHEMA_DOC
        assert "Camera Image" in SENSOR_SCHEMA_DOC
