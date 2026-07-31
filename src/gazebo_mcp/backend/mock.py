"""Offline Gazebo-style world mock."""

from __future__ import annotations

import time
from typing import Any


class MockBackend:
    name = "mock"

    def __init__(self) -> None:
        self.seed_demo()

    def seed_demo(self, profile: str = "default") -> dict[str, Any]:
        profile = (profile or "default").strip().lower()
        self._world = "fleet_demo" if profile == "fleet" else "shapes_demo"
        self._paused = False
        self._t0 = time.time()
        self._sim_time = 0.0
        self._models = self._seed_models(profile)
        return {
            "ok": True,
            "profile": profile,
            "world": self._world,
            "models": list(self._models),
        }

    def _seed_models(self, profile: str) -> dict[str, dict[str, Any]]:
        models: dict[str, dict[str, Any]] = {
            "ground_plane": {
                "name": "ground_plane",
                "type": "plane",
                "pose": {"x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0},
                "twist": self._twist(),
            },
        }
        if profile == "fleet":
            models.update(
                {
                    "robot_0": {
                        "name": "robot_0",
                        "type": "robot",
                        "pose": {"x": -1.0, "y": -1.0, "z": 0.1, "yaw": 0.0},
                    },
                    "robot_1": {
                        "name": "robot_1",
                        "type": "robot",
                        "pose": {"x": 0.0, "y": 1.0, "z": 0.1, "yaw": 1.57},
                    },
                    "robot_2": {
                        "name": "robot_2",
                        "type": "robot",
                        "pose": {"x": 1.0, "y": -1.0, "z": 0.1, "yaw": 3.14},
                    },
                }
            )
            return models
        models.update(
            {
            "box_1": {
                "name": "box_1",
                "type": "box",
                "pose": {"x": 1.0, "y": 0.0, "z": 0.5, "yaw": 0.0},
                "twist": self._twist(),
            },
            "sphere_1": {
                "name": "sphere_1",
                "type": "sphere",
                "pose": {"x": -1.0, "y": 0.5, "z": 0.5, "yaw": 0.0},
                "twist": self._twist(),
            },
            }
        )
        return models

    def _twist(
        self,
        linear_velocity: dict[str, Any] | None = None,
        angular_velocity: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, float]]:
        linear_velocity = linear_velocity or {}
        angular_velocity = angular_velocity or {}
        return {
            "linear": {
                "x": float(linear_velocity.get("x", 0.0)),
                "y": float(linear_velocity.get("y", 0.0)),
                "z": float(linear_velocity.get("z", 0.0)),
            },
            "angular": {
                "x": float(angular_velocity.get("x", 0.0)),
                "y": float(angular_velocity.get("y", 0.0)),
                "z": float(angular_velocity.get("z", 0.0)),
            },
        }

    def doctor(self) -> dict[str, Any]:
        return {
            "ok": True,
            "connected": True,
            "mode": "mock",
            "gazebo_required": False,
            "message": "Mock Gazebo world active — no Gazebo install needed",
            "world": self._world,
            "model_count": len(self._models),
            "paused": self._paused,
            "sim_time_sec": round(self._sim_time, 3),
        }

    def world_info(self) -> dict[str, Any]:
        if not self._paused:
            self._sim_time = time.time() - self._t0
        return {
            "world": self._world,
            "paused": self._paused,
            "sim_time_sec": round(self._sim_time, 3),
            "model_count": len(self._models),
            "physics": "ode-mock",
        }

    def list_worlds(self) -> dict[str, Any]:
        """List deterministic offline world fixtures and mark the active world."""
        worlds = [
            {
                "name": "shapes_demo",
                "profile": "default",
                "model_count": 3,
                "active": self._world == "shapes_demo",
            },
            {
                "name": "fleet_demo",
                "profile": "fleet",
                "model_count": 4,
                "active": self._world == "fleet_demo",
            },
        ]
        return {
            "ok": True,
            "mode": "mock",
            "current_world": self._world,
            "worlds": worlds,
        }

    def list_models(self) -> list[dict[str, Any]]:
        return list(self._models.values())

    def snapshot(self) -> dict[str, Any]:
        """Full world snapshot: models, sim time, physics params."""
        if not self._paused:
            self._sim_time = time.time() - self._t0
        return {
            "ok": True,
            "world": self._world,
            "paused": self._paused,
            "sim_time_sec": round(self._sim_time, 3),
            "model_count": len(self._models),
            "models": list(self._models.values()),
            "physics": {
                "engine": "ode-mock",
                "max_step_size": 0.001,
                "real_time_factor": 1.0,
                "gravity": {"x": 0.0, "y": 0.0, "z": -9.8},
            },
        }

    def spawn(
        self,
        name: str,
        model_type: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
    ) -> dict[str, Any]:
        if name in self._models:
            return {"ok": False, "error": f"model {name} already exists"}
        self._models[name] = {
            "name": name,
            "type": model_type or "box",
            "pose": {"x": float(x), "y": float(y), "z": float(z), "yaw": float(yaw)},
            "twist": self._twist(),
        }
        return {"ok": True, "model": self._models[name]}

    def delete(self, name: str) -> dict[str, Any]:
        if name not in self._models:
            return {"ok": False, "error": f"unknown model {name}"}
        if name == "ground_plane":
            return {"ok": False, "error": "cannot delete ground_plane"}
        del self._models[name]
        return {"ok": True, "deleted": name}

    def get_pose(self, name: str) -> dict[str, Any]:
        m = self._models.get(name)
        if not m:
            return {"ok": False, "error": f"unknown model {name}"}
        return {"ok": True, "name": name, "pose": m["pose"], "twist": m.get("twist", self._twist())}

    def set_pose(
        self,
        name: str,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        linear_velocity: dict[str, Any] | None = None,
        angular_velocity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        m = self._models.get(name)
        if not m:
            return {"ok": False, "error": f"unknown model {name}"}
        m["pose"] = {"x": float(x), "y": float(y), "z": float(z), "yaw": float(yaw)}
        m["twist"] = self._twist(linear_velocity, angular_velocity)
        return {"ok": True, "name": name, "pose": m["pose"], "twist": m["twist"]}

    def pause(self) -> dict[str, Any]:
        self._paused = True
        return {"ok": True, "paused": True, "sim_time_sec": round(self._sim_time, 3)}

    def unpause(self) -> dict[str, Any]:
        self._paused = False
        self._t0 = time.time() - self._sim_time
        return {"ok": True, "paused": False}

    def step(self, steps: int = 1) -> dict[str, Any]:
        n = max(1, int(steps))
        self._sim_time += 0.001 * n
        self._paused = True
        return {"ok": True, "steps": n, "sim_time_sec": round(self._sim_time, 3), "paused": True}

    def sensor_snapshot(
        self,
        sensor_type: str = "lidar",
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """Return synthetic sensor frames for agent workflows.

        Args:
            sensor_type: "lidar" or "camera" (default: "lidar")
            model_name: Optional model to attach sensor to (uses first
                        non-ground model if None)

        Returns:
            dict with ok, sensor_type, frame data, and schema version.

        Schema (v1):
            lidar: {
                "ok": true,
                "sensor_type": "lidar",
                "schema_version": 1,
                "model": str,
                "timestamp_sec": float,
                "frame": {
                    "points": [{"x", "y", "z", "intensity"}, ...],
                    "count": int,
                    "range_min_m": float,
                    "range_max_m": float,
                    "horizontal_fov_deg": float,
                    "vertical_fov_deg": float,
                }
            }
            camera: {
                "ok": true,
                "sensor_type": "camera",
                "schema_version": 1,
                "model": str,
                "timestamp_sec": float,
                "frame": {
                    "width": int,
                    "height": int,
                    "format": str,
                    "pixels_base64": str,  # placeholder
                    "description": str,
                }
            }
        """
        import math
        import hashlib
        import random

        # Pick a model for the sensor
        valid_models = [n for n in self._models if n != "ground_plane"]
        if model_name:
            if model_name not in self._models:
                return {"ok": False, "error": f"unknown model {model_name}"}
            target = model_name
        elif valid_models:
            target = valid_models[0]
        else:
            return {"ok": False, "error": "no valid models for sensor attachment"}

        model = self._models[target]
        pose = model.get("pose", {"x": 0, "y": 0, "z": 0, "yaw": 0})
        timestamp = self._sim_time if self._paused else (time.time() - self._t0)

        # Deterministic seed from model + sim_time for reproducibility
        seed = int(hashlib.sha256(
            f"{target}:{timestamp:.3f}".encode()
        ).hexdigest()[:8], 16)
        rng = random.Random(seed)

        if sensor_type == "lidar":
            n_points = 360  # 1 degree resolution
            points = []
            for i in range(n_points):
                angle_rad = math.radians(i)
                dist = rng.uniform(0.5, 10.0)
                px = pose["x"] + dist * math.cos(angle_rad + pose.get("yaw", 0))
                py = pose["y"] + dist * math.sin(angle_rad + pose.get("yaw", 0))
                pz = pose["z"] + rng.uniform(-0.1, 0.1)
                intensity = round(rng.uniform(0.0, 1.0), 3)
                points.append({
                    "x": round(px, 3),
                    "y": round(py, 3),
                    "z": round(pz, 3),
                    "intensity": intensity,
                })
            frame = {
                "points": points,
                "count": len(points),
                "range_min_m": 0.1,
                "range_max_m": 30.0,
                "horizontal_fov_deg": 360.0,
                "vertical_fov_deg": 30.0,
            }
        elif sensor_type == "camera":
            frame = {
                "width": 640,
                "height": 480,
                "format": "rgb8",
                "pixels_base64": "iVBORw0KGgo...=",  # placeholder
                "description": (
                    f"Synthetic camera view from {target} at "
                    f"({pose['x']:.1f}, {pose['y']:.1f}, {pose['z']:.1f}). "
                    f"Placeholder — real implementation would generate "
                    f"a scene render or connect to a Gazebo camera topic."
                ),
            }
        else:
            return {
                "ok": False,
                "error": f"unknown sensor_type '{sensor_type}'. Use 'lidar' or 'camera'",
            }

        return {
            "ok": True,
            "sensor_type": sensor_type,
            "schema_version": 1,
            "model": target,
            "timestamp_sec": round(timestamp, 3),
            "frame": frame,
        }
