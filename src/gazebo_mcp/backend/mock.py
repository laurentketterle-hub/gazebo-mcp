"""Offline Gazebo-style world mock."""

from __future__ import annotations

import time
from typing import Any

from gazebo_mcp.config import spawn_allowlist


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
        # Check spawn allowlist
        allowed = spawn_allowlist()
        if allowed is not None and model_type.lower() not in allowed:
            return {
                "ok": False,
                "error": f"model_type '{model_type}' not in GAZEBO_MCP_SPAWN_ALLOWLIST",
                "allowlist": sorted(allowed),
            }
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

    def model_exists(self, name: str) -> dict[str, Any]:
        """Check whether a model exists in the current world."""
        return {
            "ok": True,
            "name": name,
            "exists": name in self._models,
        }

    def model_info(self, name: str) -> dict[str, Any]:
        """Return detailed information about a model including pose, twist, type, and
        protection status."""
        m = self._models.get(name)
        if not m:
            return {"ok": False, "error": f"unknown model {name}"}
        return {
            "ok": True,
            "name": m["name"],
            "type": m.get("type", "unknown"),
            "pose": m.get("pose", {}),
            "twist": m.get("twist", self._twist()),
            "is_ground_plane": name == "ground_plane",
            "is_protected": name == "ground_plane",
        }

    def model_reset(self) -> dict[str, Any]:
        """Remove all user-spawned models and re-seed the world.

        Clears all models (including any modifications to seed models) and
        re-seeds the demo world to its initial state.
        """
        self.seed_demo()
        return {
            "ok": True,
            "message": "All user models cleared; world re-seeded",
            "remaining_models": list(self._models.keys()),
            "model_count": len(self._models),
        }

    def model_batch_spawn(
        self,
        models: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Spawn multiple models in a single atomic batch.

        Each model dict requires ``name``. Optional keys: ``model_type``
        (default ``"box"``), ``x``, ``y``, ``z`` (default ``0.5``),
        ``yaw`` (default ``0.0``).

        Returns per-model results plus a combined summary.
        """
        results = []
        spawned: list[str] = []
        errors: list[dict[str, Any]] = []
        for spec in models:
            r = self.spawn(
                name=spec["name"],
                model_type=spec.get("model_type", "box"),
                x=float(spec.get("x", 0.0)),
                y=float(spec.get("y", 0.0)),
                z=float(spec.get("z", 0.5)),
                yaw=float(spec.get("yaw", 0.0)),
            )
            results.append(r)
            if r.get("ok"):
                spawned.append(spec["name"])
            else:
                errors.append({"name": spec["name"], "error": r.get("error")})
        return {
            "ok": len(errors) == 0,
            "total": len(models),
            "spawned": len(spawned),
            "spawned_names": spawned,
            "errors": errors,
            "results": results,
        }

    def model_types(self) -> dict[str, Any]:
        """Return the set of supported model types and the active allowlist state."""
        allowed = spawn_allowlist()
        builtin = ["box", "sphere", "cylinder", "plane", "robot", "urdf", "sdf"]
        return {
            "ok": True,
            "builtin_types": builtin,
            "allowlist": sorted(allowed) if allowed else None,
            "allowlist_active": allowed is not None,
        }

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
