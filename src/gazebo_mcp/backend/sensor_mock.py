"""Synthetic sensor data for gazebo-mcp (LiDAR / camera mock)."""

from __future__ import annotations

import math
import random
from typing import Any


def generate_lidar_scan(
    ranges_count: int = 360,
    max_range: float = 10.0,
    min_angle: float = -3.14159,
    max_angle: float = 3.14159,
    noise: float = 0.02,
) -> dict[str, Any]:
    """Generate a synthetic 2D LiDAR scan."""
    angle_step = (max_angle - min_angle) / max(1, ranges_count - 1)
    ranges: list[float] = []
    intensities: list[float] = []
    rng = random.Random(42)

    for i in range(ranges_count):
        angle = min_angle + i * angle_step
        base_range = 3.0 + 1.5 * math.sin(angle * 3.0) * math.cos(angle * 5.0)
        if abs(math.sin(angle * 7.0)) > 0.85:
            base_range = min(base_range, 1.5 + 0.3 * rng.random())
        if math.cos(angle * 4.0) > 0.7:
            base_range = max(base_range, 6.5 + rng.random())
        jitter = rng.gauss(0, noise)
        r = max(0.1, min(max_range, base_range + jitter))
        ranges.append(round(r, 3))
        intensities.append(round(rng.uniform(0.3, 1.0), 3))

    return {
        "ok": True,
        "sensor_type": "lidar",
        "frame_id": "lidar_link",
        "ranges_count": ranges_count,
        "max_range_m": max_range,
        "angle_min_rad": min_angle,
        "angle_max_rad": max_angle,
        "angle_step_rad": round(angle_step, 6),
        "ranges": ranges,
        "intensities": intensities,
    }


def generate_camera_image(
    width: int = 640,
    height: int = 480,
    encoding: str = "rgb8",
) -> dict[str, Any]:
    """Generate synthetic camera frame metadata."""
    rng = random.Random(42)
    fx = float(width)
    fy = float(height)
    cx = width / 2.0
    cy = height / 2.0
    channels = 3 if "rgb" in encoding or "bgr" in encoding else 1

    return {
        "ok": True,
        "sensor_type": "camera",
        "frame_id": "camera_link",
        "width": width,
        "height": height,
        "encoding": encoding,
        "channels": channels,
        "intrinsics": {
            "fx": fx, "fy": fy, "cx": cx, "cy": cy,
            "distortion_model": "none",
        },
        "pixel_stats": {
            "mean_r": round(rng.uniform(80, 150), 1),
            "mean_g": round(rng.uniform(80, 150), 1),
            "mean_b": round(rng.uniform(80, 150), 1),
        },
        "data_size_bytes": width * height * channels,
        "mock_note": "Synthetic frame - no real camera connected",
    }


SENSOR_SCHEMA_DOC = """## Sensor Snapshot Schema

### LiDAR Scan
- sensor_type: "lidar"
- frame_id: TF frame name
- ranges: list of range values (meters)
- intensities: list of intensity values (0.0-1.0)

### Camera Image
- sensor_type: "camera"
- intrinsics: camera matrix + distortion model
- pixel_stats: mean RGB values
"""
