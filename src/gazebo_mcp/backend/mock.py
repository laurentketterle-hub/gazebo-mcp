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
        self, sensor_type: str = "lidar", model_name: str | None = None
    ) -> dict[str, Any]:
        """Return a deterministic synthetic sensor snapshot for the given model."""
        import base64
        import hashlib
        import math

        sensor_type = (sensor_type or "lidar").strip().lower()

        if sensor_type not in ("lidar", "camera"):
            return {"ok": False, "error": f"unknown sensor_type {sensor_type!r}"}

        # Pick a model
        non_ground = {n: m for n, m in self._models.items() if n != "ground_plane"}
        if model_name is not None:
            if model_name not in self._models:
                return {"ok": False, "error": f"unknown model {model_name!r}"}
            model = self._models[model_name]
        else:
            if not non_ground:
                return {"ok": False, "error": "no valid models (only ground_plane exists)"}
            model = next(iter(non_ground.values()))

        # Deterministic seed from model name + pose + sim time
        pose = model.get("pose", {})
        seed_str = f"{model['name']}:{pose.get('x'):.2f}:{pose.get('y'):.2f}:{pose.get('z'):.2f}:{self._sim_time:.3f}"
        seed_hash = hashlib.sha256(seed_str.encode()).digest()
        seed = int.from_bytes(seed_hash[:4], "big")

        rng_state = seed
        def _rand() -> float:
            nonlocal rng_state
            rng_state = (rng_state * 1103515245 + 12345) & 0x7FFFFFFF
            return rng_state / 0x7FFFFFFF

        result: dict[str, Any] = {
            "ok": True,
            "sensor_type": sensor_type,
            "schema_version": 1,
            "model": model["name"],
            "timestamp_sec": round(self._sim_time, 3),
        }

        if sensor_type == "lidar":
            points = []
            for i in range(360):
                angle = 2 * math.pi * i / 360
                r = 0.5 + _rand() * 29.4  # within range [0.1, 30]
                points.append({
                    "x": round(r * math.cos(angle), 4),
                    "y": round(r * math.sin(angle), 4),
                    "z": round(_rand() * 0.5 - 0.25, 4),
                    "intensity": round(_rand(), 4),
                })
            result["frame"] = {
                "count": 360,
                "points": points,
                "horizontal_fov_deg": 360.0,
                "vertical_fov_deg": 30.0,
                "range_min_m": 0.1,
                "range_max_m": 30.0,
            }
        else:  # camera
            pixels = bytes(int(_rand() * 255) for _ in range(64))
            result["frame"] = {
                "width": 640,
                "height": 480,
                "format": "rgb8",
                "pixels_base64": base64.b64encode(pixels).decode("ascii"),
                "description": "Synthetic camera view — Placeholder RGB8 image (mock Gazebo)",
            }

        return result
