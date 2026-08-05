"""
World Control Tools — physics control, gravity, step simulation.
Provides world-level operations for gazebo simulation control.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time as _time


@dataclass
class PhysicsConfig:
    gravity_x: float = 0.0
    gravity_y: float = 0.0
    gravity_z: float = -9.81
    max_step_size: float = 0.001
    real_time_factor: float = 1.0
    real_time_update_rate: float = 1000.0
    solver_type: str = "quick"
    use_adaptive_step: bool = True
    contact_surface_layer: float = 0.001
    contact_max_correcting_vel: float = 100.0
    iters: int = 50

    def to_dict(self) -> dict:
        return {
            "gravity": {"x": self.gravity_x, "y": self.gravity_y, "z": self.gravity_z},
            "max_step_size": self.max_step_size,
            "real_time_factor": self.real_time_factor,
            "real_time_update_rate": self.real_time_update_rate,
            "solver": {
                "type": self.solver_type, "iters": self.iters,
                "adaptive_step": self.use_adaptive_step,
                "contact_surface_layer": self.contact_surface_layer,
                "contact_max_correcting_vel": self.contact_max_correcting_vel
            }
        }


@dataclass
class WorldState:
    name: str = "default"
    paused: bool = False
    iterations: int = 0
    sim_time_sec: float = 0.0
    real_time_sec: float = 0.0
    physics_enabled: bool = True
    model_count: int = 0
    light_count: int = 0
    joint_count: int = 0
    link_count: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name, "paused": self.paused,
            "iterations": self.iterations,
            "sim_time": self.sim_time_sec, "real_time": self.real_time_sec,
            "physics_enabled": self.physics_enabled,
            "entity_counts": {
                "models": self.model_count, "lights": self.light_count,
                "joints": self.joint_count, "links": self.link_count
            }
        }


@dataclass
class WorldInfo:
    name: str
    version: str = "gazebo-9.x"
    sim_time: float = 0.0
    paused: bool = False
    physics: PhysicsConfig = field(default_factory=PhysicsConfig)

    def to_dict(self) -> dict:
        return {"name": self.name, "version": self.version,
                "sim_time": self.sim_time, "paused": self.paused,
                "physics": self.physics.to_dict()}


_world = WorldState(name="default", sim_time_sec=0.0)
_physics = PhysicsConfig()
_step_count = 0


def reset_world() -> dict:
    global _world, _step_count
    _world = WorldState(name="default", sim_time_sec=0.0)
    _step_count = 0
    return {"status": "ok", "message": "World reset to initial state"}


def pause_world() -> dict:
    _world.paused = True
    return {"status": "paused", "sim_time": _world.sim_time_sec}


def unpause_world() -> dict:
    _world.paused = False
    return {"status": "running", "sim_time": _world.sim_time_sec}


def get_world_state() -> dict:
    return _world.to_dict()


def step_world(steps: int = 1, step_size_sec: float = 0.001) -> dict:
    global _world, _step_count
    if _world.paused:
        return {"error": "World is paused — unpause first"}
    for _ in range(steps):
        _world.sim_time_sec += step_size_sec
        _world.iterations += 1
        _step_count += 1
    return {"status": "stepped", "steps_executed": steps,
            "sim_time": _world.sim_time_sec, "total_iterations": _world.iterations}


def get_physics_config() -> dict:
    return _physics.to_dict()


def set_physics_config(
    gravity_x: Optional[float] = None, gravity_y: Optional[float] = None,
    gravity_z: Optional[float] = None, max_step_size: Optional[float] = None,
    real_time_factor: Optional[float] = None, solver_iters: Optional[int] = None
) -> dict:
    changes = {}
    if gravity_x is not None: _physics.gravity_x = gravity_x; changes["gravity_x"] = gravity_x
    if gravity_y is not None: _physics.gravity_y = gravity_y; changes["gravity_y"] = gravity_y
    if gravity_z is not None: _physics.gravity_z = gravity_z; changes["gravity_z"] = gravity_z
    if max_step_size is not None: _physics.max_step_size = max_step_size; changes["max_step_size"] = max_step_size
    if real_time_factor is not None: _physics.real_time_factor = real_time_factor; changes["real_time_factor"] = real_time_factor
    if solver_iters is not None: _physics.iters = solver_iters; changes["solver_iters"] = solver_iters
    return {"status": "updated", "changes": changes, "physics": _physics.to_dict()}


def get_world_info() -> dict:
    return WorldInfo(name=_world.name, sim_time=_world.sim_time_sec,
                     paused=_world.paused, physics=_physics).to_dict()


@dataclass
class Light:
    name: str
    light_type: str = "directional"
    diffuse: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0])
    specular: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0])
    attenuation_constant: float = 1.0
    attenuation_linear: float = 0.0
    attenuation_quadratic: float = 0.0
    direction: List[float] = field(default_factory=lambda: [0.0, 0.0, -1.0])

    def to_dict(self) -> dict:
        return {
            "name": self.name, "type": self.light_type,
            "diffuse": self.diffuse, "specular": self.specular,
            "attenuation": {"constant": self.attenuation_constant,
                           "linear": self.attenuation_linear,
                           "quadratic": self.attenuation_quadratic},
            "direction": self.direction
        }


_lights: Dict[str, Light] = {}


def create_light(name: str, light_type: str = "directional",
                 diffuse_r: float = 1.0, diffuse_g: float = 1.0, diffuse_b: float = 1.0,
                 direction_x: float = 0.0, direction_y: float = 0.0, direction_z: float = -1.0) -> dict:
    if name in _lights:
        return {"error": f"Light '{name}' already exists"}
    light = Light(name=name, light_type=light_type,
                  diffuse=[diffuse_r, diffuse_g, diffuse_b, 1.0],
                  direction=[direction_x, direction_y, direction_z])
    _lights[name] = light
    _world.light_count = len(_lights)
    return {"status": "created", "light": light.to_dict()}


def list_lights() -> dict:
    return {"lights": [l.to_dict() for l in _lights.values()], "count": len(_lights)}


def delete_light(name: str) -> dict:
    if name in _lights:
        del _lights[name]
        _world.light_count = len(_lights)
        return {"status": "deleted", "name": name}
    return {"error": f"Light '{name}' not found"}


@dataclass
class Joint:
    name: str
    joint_type: str = "revolute"
    parent: str = "world"
    child: str = ""
    axis: List[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    lower_limit: float = -1.57
    upper_limit: float = 1.57
    effort_limit: float = 100.0
    velocity_limit: float = 10.0
    position: float = 0.0
    velocity: float = 0.0
    effort: float = 0.0

    def to_dict(self) -> dict:
        return {"name": self.name, "type": self.joint_type,
                "parent": self.parent, "child": self.child,
                "axis": self.axis, "limits": {"lower": self.lower_limit, "upper": self.upper_limit,
                                              "effort": self.effort_limit, "velocity": self.velocity_limit},
                "state": {"position": self.position, "velocity": self.velocity, "effort": self.effort}}


_joints: Dict[str, Joint] = {}


def create_joint(name: str, joint_type: str = "revolute",
                 parent: str = "world", child: str = "",
                 axis_x: float = 0.0, axis_y: float = 0.0, axis_z: float = 1.0) -> dict:
    if name in _joints:
        return {"error": f"Joint '{name}' already exists"}
    joint = Joint(name=name, joint_type=joint_type, parent=parent,
                  child=child, axis=[axis_x, axis_y, axis_z])
    _joints[name] = joint
    _world.joint_count = len(_joints)
    return {"status": "created", "joint": joint.to_dict()}


def list_joints() -> dict:
    return {"joints": [j.to_dict() for j in _joints.values()], "count": len(_joints)}


def set_joint_position(name: str, position: float) -> dict:
    if name not in _joints:
        return {"error": f"Joint '{name}' not found"}
    _joints[name].position = position
    return {"status": "ok", "joint": name, "position": position}
