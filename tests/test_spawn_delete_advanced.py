"""Advanced tests for model_spawn/model_delete: edge cases, batch ops, and MCP server integration."""
from __future__ import annotations

import json

import pytest

from gazebo_mcp.backend.mock import MockBackend


class TestModelExists:
    """model_exists validates presence without side effects."""

    def setup_method(self) -> None:
        self.mock = MockBackend()
        self.mock.seed_demo()

    def test_seed_models_exist(self) -> None:
        assert self.mock.model_exists("ground_plane")["exists"] is True
        assert self.mock.model_exists("box_1")["exists"] is True
        assert self.mock.model_exists("sphere_1")["exists"] is True

    def test_nonexistent_returns_false(self) -> None:
        r = self.mock.model_exists("phantom")
        assert r["ok"] is True
        assert r["exists"] is False

    def test_spawned_model_reported_existing(self) -> None:
        self.mock.spawn("new_model", "box", 0, 0, 0)
        assert self.mock.model_exists("new_model")["exists"] is True

    def test_deleted_model_reported_nonexistent(self) -> None:
        self.mock.spawn("tmp", "box", 0, 0, 0)
        self.mock.delete("tmp")
        assert self.mock.model_exists("tmp")["exists"] is False


class TestModelInfo:
    """model_info returns full metadata for a model."""

    def setup_method(self) -> None:
        self.mock = MockBackend()
        self.mock.seed_demo()

    def test_seed_model_info_has_fields(self) -> None:
        info = self.mock.model_info("box_1")
        assert info["ok"] is True
        assert info["name"] == "box_1"
        assert info["type"] == "box"
        assert "pose" in info
        assert "twist" in info

    def test_ground_plane_is_protected(self) -> None:
        info = self.mock.model_info("ground_plane")
        assert info["is_ground_plane"] is True
        assert info["is_protected"] is True

    def test_spawned_model_not_protected(self) -> None:
        self.mock.spawn("user_model", "sphere", 0, 0, 0.5)
        info = self.mock.model_info("user_model")
        assert info["is_ground_plane"] is False
        assert info["is_protected"] is False

    def test_unknown_model_errors(self) -> None:
        r = self.mock.model_info("nope")
        assert r["ok"] is False
        assert "unknown model" in r["error"]


class TestModelReset:
    """model_reset clears user models and re-seeds."""

    def setup_method(self) -> None:
        self.mock = MockBackend()
        self.mock.seed_demo()

    def test_reset_clears_spawned_models(self) -> None:
        self.mock.spawn("a", "box", 0, 0, 0)
        self.mock.spawn("b", "sphere", 1, 1, 1)
        r = self.mock.model_reset()
        assert r["ok"] is True
        assert "a" not in self.mock._models
        assert "b" not in self.mock._models
        # Seed models restored
        assert "ground_plane" in self.mock._models
        assert "box_1" in self.mock._models

    def test_reset_restores_world(self) -> None:
        self.mock.spawn("temp", "cylinder", 10, 10, 10)
        self.mock.model_reset()
        assert self.mock._world == "shapes_demo"
        assert len(self.mock.list_models()) == self.mock.snapshot()["model_count"]

    def test_reset_after_fleet_profile(self) -> None:
        self.mock.seed_demo("fleet")
        self.mock.spawn("drone", "robot", 5, 5, 0.5)
        self.mock.model_reset()
        # Reset always goes to default shapes_demo
        assert self.mock._world == "shapes_demo"


class TestModelBatchSpawn:
    """model_batch_spawn handles multi-model operations."""

    def setup_method(self) -> None:
        self.mock = MockBackend()
        self.mock.seed_demo()

    def test_batch_spawn_multiple(self) -> None:
        models = [
            {"name": "batch_a", "model_type": "box", "x": 0, "y": 0},
            {"name": "batch_b", "model_type": "sphere", "x": 1, "y": 1},
            {"name": "batch_c", "model_type": "cylinder", "x": -1, "y": -1},
        ]
        r = self.mock.model_batch_spawn(models)
        assert r["ok"] is True
        assert r["total"] == 3
        assert r["spawned"] == 3
        assert set(r["spawned_names"]) == {"batch_a", "batch_b", "batch_c"}

    def test_batch_uses_defaults(self) -> None:
        models = [{"name": "auto"}]
        r = self.mock.model_batch_spawn(models)
        assert r["ok"] is True
        m = self.mock._models["auto"]
        assert m["type"] == "box"
        assert m["pose"]["z"] == 0.5

    def test_batch_reports_partial_failures(self) -> None:
        self.mock.spawn("existing", "box", 0, 0, 0)
        models = [
            {"name": "existing", "model_type": "box", "x": 0, "y": 0},
            {"name": "new_one", "model_type": "sphere", "x": 1, "y": 1},
        ]
        r = self.mock.model_batch_spawn(models)
        assert r["ok"] is False
        assert r["spawned"] == 1
        assert len(r["errors"]) == 1
        assert r["errors"][0]["name"] == "existing"

    def test_batch_empty_list(self) -> None:
        r = self.mock.model_batch_spawn([])
        assert r["ok"] is True
        assert r["total"] == 0
        assert r["spawned"] == 0


class TestModelTypes:
    """model_types reports builtin types and allowlist state."""

    def test_reports_builtin_types(self) -> None:
        mock = MockBackend()
        r = mock.model_types()
        assert r["ok"] is True
        assert "box" in r["builtin_types"]
        assert "sphere" in r["builtin_types"]
        assert "cylinder" in r["builtin_types"]

    def test_no_allowlist_by_default(self) -> None:
        mock = MockBackend()
        r = mock.model_types()
        assert r["allowlist"] is None
        assert r["allowlist_active"] is False

    def test_allowlist_reported_when_set(self, monkeypatch) -> None:
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "box,cylinder")
        mock = MockBackend()
        r = mock.model_types()
        assert r["allowlist_active"] is True
        assert r["allowlist"] == ["box", "cylinder"]


class TestSpawnDeleteEdgeCases:
    """Edge cases and stress scenarios for spawn/delete."""

    def setup_method(self) -> None:
        self.mock = MockBackend()
        self.mock.seed_demo()

    def test_spawn_with_negative_coordinates(self) -> None:
        r = self.mock.spawn("neg", "box", x=-100.0, y=-200.0, z=-50.0)
        assert r["ok"] is True
        assert r["model"]["pose"]["x"] == -100.0
        assert r["model"]["pose"]["y"] == -200.0
        assert r["model"]["pose"]["z"] == -50.0

    def test_spawn_with_large_coordinates(self) -> None:
        r = self.mock.spawn("big", "sphere", x=1e6, y=1e6, z=1e6, yaw=360.0)
        assert r["ok"] is True
        assert r["model"]["pose"]["x"] == 1e6

    def test_spawn_with_zero_dimensions(self) -> None:
        r = self.mock.spawn("zero", "box", x=0.0, y=0.0, z=0.0, yaw=0.0)
        assert r["ok"] is True
        pose = r["model"]["pose"]
        assert pose["x"] == 0.0 and pose["y"] == 0.0 and pose["z"] == 0.0

    def test_rapid_spawn_delete_cycle(self) -> None:
        """Rapid spawn-delete cycles stay consistent."""
        for i in range(10):
            name = f"rapid_{i}"
            assert self.mock.spawn(name, "box", i, i, 0.5)["ok"] is True
            assert self.mock.delete(name)["ok"] is True
            assert not self.mock.model_exists(name)["exists"]

    def test_spawn_all_builtin_types(self) -> None:
        types = ["box", "sphere", "cylinder", "robot", "urdf", "sdf"]
        for i, t in enumerate(types):
            r = self.mock.spawn(f"type_{t}", t, i, 0, 0.5)
            assert r["ok"] is True, f"failed for type {t}"
            assert self.mock._models[f"type_{t}"]["type"] == t

    def test_delete_all_spawned_models(self) -> None:
        spawned = []
        for i in range(5):
            name = f"delme_{i}"
            self.mock.spawn(name, "box", i, 0, 0)
            spawned.append(name)
        for name in spawned:
            assert self.mock.delete(name)["ok"] is True
        # Only seed models remain
        assert self.mock.snapshot()["model_count"] == 3

    def test_spawn_preserves_twist_defaults(self) -> None:
        r = self.mock.spawn("twisted", "cylinder", 0, 0, 0.5)
        twist = r["model"]["twist"]
        assert twist["linear"]["x"] == 0.0
        assert twist["linear"]["y"] == 0.0
        assert twist["linear"]["z"] == 0.0
        assert twist["angular"]["x"] == 0.0
        assert twist["angular"]["y"] == 0.0
        assert twist["angular"]["z"] == 0.0


class TestAllowlistEdgeCases:
    """Edge cases for spawn allowlist configuration."""

    def test_allowlist_empty_string_is_none(self, monkeypatch) -> None:
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "")
        mock = MockBackend()
        r = mock.spawn("ok", "box", 0, 0, 0)
        assert r["ok"] is True

    def test_allowlist_whitespace_only(self, monkeypatch) -> None:
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "  ,  ,  ")
        mock = MockBackend()
        # Whitespace-only should behave like no allowlist
        r = mock.spawn("ok", "cylinder", 0, 0, 0)
        assert r["ok"] is True

    def test_allowlist_single_entry(self, monkeypatch) -> None:
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "sphere")
        mock = MockBackend()
        assert mock.spawn("s", "sphere", 0, 0, 0)["ok"] is True
        assert mock.spawn("b", "box", 0, 0, 0)["ok"] is False

    def test_allowlist_extra_whitespace(self, monkeypatch) -> None:
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "  box ,  sphere  ")
        mock = MockBackend()
        assert mock.spawn("s", "sphere", 0, 0, 0)["ok"] is True
        assert mock.spawn("b", "box", 0, 0, 0)["ok"] is True
        assert mock.spawn("c", "cylinder", 0, 0, 0)["ok"] is False

    def test_allowlist_block_returns_types(self) -> None:
        """When blocked, error includes the allowlist values."""
        import os
        os.environ["GAZEBO_MCP_SPAWN_ALLOWLIST"] = "box"
        mock = MockBackend()
        r = mock.spawn("nope", "sphere", 0, 0, 0)
        assert r["ok"] is False
        assert "allowlist" in r
        assert "box" in r["allowlist"]
        del os.environ["GAZEBO_MCP_SPAWN_ALLOWLIST"]


class TestConsistencyAfterBatchOps:
    """State remains consistent after batch and multi-operation sequences."""

    def setup_method(self) -> None:
        self.mock = MockBackend()
        self.mock.seed_demo()

    def test_world_snapshot_after_batch(self) -> None:
        models = [{"name": f"b{i}", "model_type": "box", "x": i, "y": 0} for i in range(4)]
        self.mock.model_batch_spawn(models)
        snap = self.mock.snapshot()
        assert snap["model_count"] == 3 + 4  # 3 seed + 4 batch
        names = {m["name"] for m in snap["models"]}
        assert names.issuperset({"b0", "b1", "b2", "b3"})

    def test_batch_then_partial_delete(self) -> None:
        models = [{"name": f"k{i}", "model_type": "sphere", "x": i, "y": 0} for i in range(3)]
        self.mock.model_batch_spawn(models)
        self.mock.delete("k1")
        assert len(self.mock.list_models()) == self.mock.snapshot()["model_count"]
        snap = self.mock.snapshot()
        names = {m["name"] for m in snap["models"]}
        assert "k0" in names and "k1" not in names and "k2" in names
