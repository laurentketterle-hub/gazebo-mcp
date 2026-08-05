"""Tests for sensor_fusion module."""
import pytest
from src.sensor_fusion import (
    feed_imu_sensor, feed_lidar_scan, feed_camera_frame,
    get_fused_perception, reset_sensor_fusion,
    generate_mock_lidar, generate_mock_imu,
    IMUReading, LidarScan, CameraImage, FusedPerception, SensorFusion
)


class TestIMU:
    def test_feed_imu(self):
        result = feed_imu_sensor(linear_accel_x=1.0, linear_accel_y=0.5, linear_accel_z=9.8)
        assert result["status"] == "ok"
        assert result["sensor"] == "imu"

    def test_imu_reading_dataclass(self):
        imu = IMUReading(linear_acceleration_x=1.0)
        d = imu.to_dict()
        assert d["linear_acceleration"]["x"] == 1.0


class TestLidar:
    def test_feed_lidar(self):
        result = feed_lidar_scan([1.0, 2.0, 3.0, 1.5, 0.8])
        assert result["status"] == "ok"
        assert result["point_count"] == 5

    def test_lidar_dataclass(self):
        lidar = LidarScan(ranges=[1.0, 2.0])
        d = lidar.to_dict()
        assert d["point_count"] == 2


class TestCamera:
    def test_feed_camera(self):
        result = feed_camera_frame(width=1280, height=720)
        assert result["status"] == "ok"
        assert result["resolution"] == "1280x720"


class TestFusion:
    def test_fused_output(self):
        reset_sensor_fusion()
        feed_imu_sensor(linear_accel_x=0.5)
        feed_lidar_scan([1.0, 2.0, 3.0, 0.5, 10.0])
        result = get_fused_perception()
        assert "pose" in result
        assert "obstacles" in result
        assert len(result["sources"]) >= 2

    def test_reset(self):
        reset_sensor_fusion()
        feed_imu_sensor()
        reset_sensor_fusion()
        result = get_fused_perception()
        assert result["sources"] == []

    def test_confidence(self):
        reset_sensor_fusion()
        result = get_fused_perception()
        assert result["confidence"] == 0.0
        feed_imu_sensor()
        feed_lidar_scan([1.0, 2.0])
        feed_camera_frame()
        result2 = get_fused_perception()
        assert result2["confidence"] == 1.0


class TestMockGeneration:
    def test_mock_lidar(self):
        result = generate_mock_lidar(num_points=180)
        assert result["generated"] is True
        assert result["num_points"] == 180

    def test_mock_imu(self):
        result = generate_mock_imu()
        assert result["status"] == "ok"
        assert result["sensor"] == "imu"


class TestFusedPerceptionDataclass:
    def test_to_dict(self):
        fp = FusedPerception(pose_x=1.0, pose_y=2.0,
                            velocity_x=0.5, confidence=0.8,
                            sensor_sources=["imu", "lidar"])
        d = fp.to_dict()
        assert d["pose"]["x"] == 1.0
        assert d["velocity"]["y"] == 0.0
        assert d["confidence"] == 0.8
