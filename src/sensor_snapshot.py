"""
Sensor Snapshot Tool - synthetic sensor frames for agent workflows.
Returns mock lidar ranges and camera image data.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import time as _time


@dataclass
class LidarFrame:
    ranges: List[float] = field(default_factory=list)
    angle_min: float = -3.14
    angle_max: float = 3.14
    angle_increment: float = 0.017


@dataclass
class CameraFrame:
    width: int = 640
    height: int = 480
    encoding: str = "rgb8"
    data_uri: str = "data:image/png;base64,iVBORw0KGgo=mock"


@dataclass
class SensorSnapshot:
    timestamp: float = 0.0
    lidar: Optional[LidarFrame] = None
    camera: Optional[CameraFrame] = None


def get_sensor_snapshot(include_lidar: bool = True, include_camera: bool = True) -> dict:
    snapshot = SensorSnapshot(timestamp=_time.time())
    result = {"timestamp": snapshot.timestamp, "sensors": {}}

    if include_lidar:
        lidar = LidarFrame(
            ranges=[1.0 + i * 0.5 for i in range(36)],
            angle_min=-3.14, angle_max=3.14, angle_increment=0.017
        )
        result["sensors"]["lidar"] = {
            "ranges": lidar.ranges,
            "angle_min": lidar.angle_min,
            "angle_max": lidar.angle_max,
            "angle_increment": lidar.angle_increment,
            "count": len(lidar.ranges)
        }

    if include_camera:
        result["sensors"]["camera"] = {
            "width": 640, "height": 480,
            "encoding": "rgb8",
            "data_uri": "data:image/png;base64,iVBORw0KGgo=mock"
        }

    result["schema_version"] = "1.0"
    return result
