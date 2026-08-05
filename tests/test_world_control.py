"""Tests for world_control module."""
import pytest
from src.world_control import (
    reset_world, pause_world, unpause_world, get_world_state,
    step_world, get_physics_config, set_physics_config, get_world_info,
    create_light, list_lights, delete_light,
    create_joint, list_joints, set_joint_position,
    PhysicsConfig, WorldState, WorldInfo, Light, Joint
)


class TestWorldControl:
    def test_reset_world(self):
        result = reset_world()
        assert result["status"] == "ok"
        assert get_world_state()["sim_time"] == 0.0

    def test_pause_unpause(self):
        unpause_world()
        assert pause_world()["status"] == "paused"
        assert get_world_state()["paused"] is True
        assert unpause_world()["status"] == "running"

    def test_step_world(self):
        unpause_world()
        result = step_world(steps=10, step_size_sec=0.01)
        assert result["steps_executed"] == 10

    def test_step_while_paused(self):
        pause_world()
        assert "error" in step_world(steps=5)
        unpause_world()

    def test_physics_get(self):
        config = get_physics_config()
        assert config["gravity"]["z"] == -9.81

    def test_physics_set(self):
        set_physics_config(gravity_z=-1.62, max_step_size=0.005)
        config = get_physics_config()
        assert config["gravity"]["z"] == -1.62
        set_physics_config(gravity_z=-9.81, max_step_size=0.001)

    def test_world_info(self):
        info = get_world_info()
        assert "name" in info


class TestLightManagement:
    def test_create_light(self):
        result = create_light("sun", light_type="directional",
                             direction_x=0.5, direction_y=0.5, direction_z=-1.0)
        assert result["status"] == "created"

    def test_duplicate_light(self):
        create_light("test_dup", light_type="point")
        assert "error" in create_light("test_dup")

    def test_list_lights(self):
        create_light("lamp_a", light_type="spot")
        result = list_lights()
        assert result["count"] >= 1

    def test_delete_light(self):
        create_light("to_delete")
        assert delete_light("to_delete")["status"] == "deleted"

    def test_delete_nonexistent(self):
        assert "error" in delete_light("phantom")


class TestJointManagement:
    def test_create_joint(self):
        result = create_joint("hinge", parent="base", child="arm")
        assert result["status"] == "created"

    def test_duplicate_joint(self):
        create_joint("dup_joint")
        assert "error" in create_joint("dup_joint")

    def test_list_joints(self):
        create_joint("j1"); create_joint("j2")
        assert list_joints()["count"] >= 2

    def test_set_position(self):
        create_joint("slider", joint_type="prismatic")
        result = set_joint_position("slider", 0.5)
        assert result["position"] == 0.5

    def test_set_position_nonexistent(self):
        assert "error" in set_joint_position("ghost", 1.0)
