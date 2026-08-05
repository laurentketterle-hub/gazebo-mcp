"""
Sensor Fusion Module — combine multiple sensor readings into unified perception.
Provides fused state estimation from lidar, camera, and IMU data.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time as _time
import math


@dataclass
class IMUReading:
    """Inertial Measurement Unit reading."""
    timestamp: float = 0.0
    orientation_x: float = 0.0
    orientation_y: float = 0.0
    orientation_z: float = 0.0
    orientation_w: float = 1.0
    angular_velocity_x: float = 0.0
    angular_velocity_y: float = 0.0
    angular_velocity_z: float = 0.0
    linear_acceleration_x: float = 0.0
    linear_acceleration_y: float = 0.0
    linear_acceleration_z: float = 0.0

    def to_dict(self) -> dict:
        return {
            "orientation": {"x": self.orientation_x, "y": self.orientation_y,
                           "z": self.orientation_z, "w": self.orientation_w},
            "angular_velocity": {"x": self.angular_velocity_x,
                                "y": self.angular_velocity_y,
                                "z": self.angular_velocity_z},
            "linear_acceleration": {"x": self.linear_acceleration_x,
                                   "y": self.linear_acceleration_y,
                                   "z": self.linear_acceleration_z}
        }


@dataclass
class LidarScan:
    timestamp: float = 0.0
    ranges: List[float] = field(default_factory=list)
    intensities: List[float] = field(default_factory=list)
    angle_min: float = -3.14
    angle_max: float = 3.14
    angle_increment: float = 0.017
    range_min: float = 0.1
    range_max: float = 30.0
    frame_id: str = "lidar_link"

    def to_dict(self) -> dict:
        return {
            "ranges": self.ranges, "intensities": self.intensities,
            "angle_min": self.angle_min, "angle_max": self.angle_max,
            "angle_increment": self.angle_increment,
            "range_min": self.range_min, "range_max": self.range_max,
            "frame_id": self.frame_id,
            "point_count": len(self.ranges)
        }


@dataclass
class CameraImage:
    timestamp: float = 0.0
    width: int = 640
    height: int = 480
    encoding: str = "rgb8"
    data_uri: str = ""
    frame_id: str = "camera_link"

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height,
                "encoding": self.encoding, "data_uri": self.data_uri,
                "frame_id": self.frame_id}


@dataclass
class FusedPerception:
    """Result of sensor fusion."""
    timestamp: float = 0.0
    pose_x: float = 0.0
    pose_y: float = 0.0
    pose_z: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0
    obstacle_distances: List[float] = field(default_factory=list)
    nearest_obstacle: float = float('inf')
    obstacle_direction: float = 0.0
    confidence: float = 0.0
    sensor_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "pose": {"x": self.pose_x, "y": self.pose_y, "z": self.pose_z},
            "velocity": {"x": self.velocity_x, "y": self.velocity_y, "z": self.velocity_z},
            "obstacles": {
                "distances": self.obstacle_distances[:10],
                "nearest": self.nearest_obstacle if self.nearest_obstacle != float('inf') else None,
                "direction_rad": self.obstacle_direction
            },
            "confidence": self.confidence,
            "sources": self.sensor_sources
        }


class SensorFusion:
    """Sensor fusion engine combining lidar, camera, and IMU."""

    def __init__(self):
        self._last_imu: Optional[IMUReading] = None
        self._last_lidar: Optional[LidarScan] = None
        self._last_camera: Optional[CameraImage] = None
        self._pose_x = 0.0
        self._pose_y = 0.0
        self._pose_z = 0.0
        self._vel_x = 0.0
        self._vel_y = 0.0
        self._vel_z = 0.0

    def feed_imu(self, imu: IMUReading):
        self._last_imu = imu
        # Simple dead-reckoning from acceleration
        dt = 0.01
        self._vel_x += imu.linear_acceleration_x * dt
        self._vel_y += imu.linear_acceleration_y * dt
        self._vel_z += imu.linear_acceleration_z * dt
        self._pose_x += self._vel_x * dt
        self._pose_y += self._vel_y * dt
        self._pose_z += self._vel_z * dt

    def feed_lidar(self, lidar: LidarScan):
        self._last_lidar = lidar

    def feed_camera(self, camera: CameraImage):
        self._last_camera = camera

    def get_fused(self) -> FusedPerception:
        sources = []
        if self._last_imu: sources.append("imu")
        if self._last_lidar: sources.append("lidar")
        if self._last_camera: sources.append("camera")

        obstacles = self._last_lidar.ranges if self._last_lidar else []
        nearest = min(obstacles) if obstacles else float('inf')
        direction = 0.0
        if obstacles and nearest != float('inf'):
            idx = obstacles.index(nearest)
            direction = self._last_lidar.angle_min + idx * self._last_lidar.angle_increment

        confidence = min(1.0, len(sources) / 3.0)

        return FusedPerception(
            timestamp=_time.time(),
            pose_x=self._pose_x, pose_y=self._pose_y, pose_z=self._pose_z,
            velocity_x=self._vel_x, velocity_y=self._vel_y, velocity_z=self._vel_z,
            obstacle_distances=obstacles[:20],
            nearest_obstacle=nearest if nearest != float('inf') else 0,
            obstacle_direction=direction,
            confidence=confidence,
            sensor_sources=sources
        )

    def reset(self):
        self._last_imu = None
        self._last_lidar = None
        self._last_camera = None
        self._pose_x = 0.0; self._pose_y = 0.0; self._pose_z = 0.0
        self._vel_x = 0.0; self._vel_y = 0.0; self._vel_z = 0.0


_fusion = SensorFusion()


def feed_imu_sensor(orientation_x: float = 0.0, orientation_y: float = 0.0,
                    orientation_z: float = 0.0, orientation_w: float = 1.0,
                    angular_vel_x: float = 0.0, angular_vel_y: float = 0.0,
                    angular_vel_z: float = 0.0,
                    linear_accel_x: float = 0.0, linear_accel_y: float = 0.0,
                    linear_accel_z: float = 0.0) -> dict:
    imu = IMUReading(timestamp=_time.time(),
                     orientation_x=orientation_x, orientation_y=orientation_y,
                     orientation_z=orientation_z, orientation_w=orientation_w,
                     angular_velocity_x=angular_vel_x, angular_velocity_y=angular_vel_y,
                     angular_velocity_z=angular_vel_z,
                     linear_acceleration_x=linear_accel_x, linear_acceleration_y=linear_accel_y,
                     linear_acceleration_z=linear_accel_z)
    _fusion.feed_imu(imu)
    return {"status": "ok", "sensor": "imu", "reading": imu.to_dict()}


def feed_lidar_scan(ranges: List[float], intensities: Optional[List[float]] = None,
                    angle_min: float = -3.14, angle_max: float = 3.14,
                    angle_increment: float = 0.017) -> dict:
    lidar = LidarScan(timestamp=_time.time(), ranges=ranges,
                      intensities=intensities or [1.0] * len(ranges),
                      angle_min=angle_min, angle_max=angle_max,
                      angle_increment=angle_increment)
    _fusion.feed_lidar(lidar)
    return {"status": "ok", "sensor": "lidar", "point_count": len(ranges)}


def feed_camera_frame(width: int = 640, height: int = 480,
                      encoding: str = "rgb8", data_uri: str = "") -> dict:
    camera = CameraImage(timestamp=_time.time(), width=width,
                         height=height, encoding=encoding, data_uri=data_uri)
    _fusion.feed_camera(camera)
    return {"status": "ok", "sensor": "camera", "resolution": f"{width}x{height}"}


def get_fused_perception() -> dict:
    fused = _fusion.get_fused()
    return fused.to_dict()


def reset_sensor_fusion() -> dict:
    _fusion.reset()
    return {"status": "reset"}


def generate_mock_lidar(num_points: int = 360, min_range: float = 0.5,
                        max_range: float = 15.0) -> dict:
    """Generate synthetic lidar data for testing."""
    import random
    random.seed(int(_time.time() * 1000))
    ranges = [random.uniform(min_range, max_range) for _ in range(num_points)]
    result = feed_lidar_scan(ranges)
    result["generated"] = True
    result["num_points"] = num_points
    return result


def generate_mock_imu() -> dict:
    """Generate synthetic IMU data for testing."""
    import random
    random.seed(int(_time.time() * 1000))
    return feed_imu_sensor(
        linear_accel_x=random.uniform(-0.5, 0.5),
        linear_accel_y=random.uniform(-0.5, 0.5),
        linear_accel_z=random.uniform(9.5, 10.1),
        angular_vel_z=random.uniform(-0.1, 0.1)
    )
