"""Tests for model_spawn/model_delete: mock state consistency across tools."""

import pytest
from gazebo_mcp.backend.mock import MockBackend


class TestModelSpawnDelete:
    """State consistency across model_spawn → model_delete → list_models → snapshot."""

    def setup_method(self):
        self.mock = MockBackend()
        self.mock.seed_demo()

    def test_spawn_adds_to_list(self):
        """model_spawn should appear in list_models and snapshot."""
        r = self.mock.spawn("test_box", "box", 2.0, 3.0, 0.5)
        assert r["ok"] is True
        assert r["model"]["name"] == "test_box"

        models = self.mock.list_models()
        names = {m["name"] for m in models}
        assert "test_box" in names

    def test_delete_removes_from_list(self):
        """model_delete should remove from list_models."""
        self.mock.spawn("tmp", "sphere", 0, 0, 0)
        assert "tmp" in self.mock._models

        r = self.mock.delete("tmp")
        assert r["ok"] is True
        assert "tmp" not in self.mock._models

    def test_delete_nonexistent_errors(self):
        """Deleting unknown model returns error."""
        r = self.mock.delete("ghost")
        assert r["ok"] is False
        assert "unknown model" in r["error"]

    def test_cannot_delete_ground_plane(self):
        """Ground plane is protected."""
        r = self.mock.delete("ground_plane")
        assert r["ok"] is False
        assert "cannot delete" in r["error"]

    def test_spawn_duplicate_errors(self):
        """Cannot spawn two models with same name."""
        self.mock.spawn("dup", "box", 0, 0, 0)
        r = self.mock.spawn("dup", "box", 1, 1, 1)
        assert r["ok"] is False
        assert "already exists" in r["error"]

    def test_snapshot_reflects_spawn(self):
        """World snapshot shows spawned models."""
        self.mock.spawn("s1", "cylinder", 0, 0, 0.5)
        snap = self.mock.snapshot()
        names = {m["name"] for m in snap["models"]}
        assert "s1" in names
        assert snap["model_count"] >= 1

    def test_snapshot_reflects_delete(self):
        """World snapshot does NOT show deleted models."""
        self.mock.spawn("s1", "cylinder", 0, 0, 0.5)
        self.mock.delete("s1")
        snap = self.mock.snapshot()
        names = {m["name"] for m in snap["models"]}
        assert "s1" not in names

    def test_spawn_delete_roundtrip(self):
        """Spawn → snapshot → delete → snapshot: state stays consistent."""
        r = self.mock.spawn("roundtrip", "sphere", 1.0, 2.0, 0.5, yaw=1.57)
        assert r["ok"]

        snap1 = self.mock.snapshot()
        assert any(m["name"] == "roundtrip" for m in snap1["models"])

        r = self.mock.delete("roundtrip")
        assert r["ok"]

        snap2 = self.mock.snapshot()
        assert not any(m["name"] == "roundtrip" for m in snap2["models"])

    def test_model_count_consistent(self):
        """model_count in snapshot matches len(list_models)."""
        initial = self.mock.snapshot()["model_count"]
        assert len(self.mock.list_models()) == initial

        self.mock.spawn("a", "box", 0, 0, 0)
        self.mock.spawn("b", "box", 1, 0, 0)
        assert self.mock.snapshot()["model_count"] == initial + 2
        assert len(self.mock.list_models()) == initial + 2

        self.mock.delete("a")
        assert self.mock.snapshot()["model_count"] == initial + 1
        assert len(self.mock.list_models()) == initial + 1

    def test_spawn_pose_preserved(self):
        """Spawned model pose matches what was passed."""
        r = self.mock.spawn("posed", "box", x=3.0, y=4.0, z=0.5, yaw=0.785)
        assert r["model"]["pose"]["x"] == 3.0
        assert r["model"]["pose"]["y"] == 4.0
        assert r["model"]["pose"]["z"] == 0.5
        assert r["model"]["pose"]["yaw"] == 0.785


class TestSpawnAllowlist:
    """Spawn allowlist gates model_type."""

    def test_no_allowlist_allows_all(self, monkeypatch):
        """No allowlist → all types allowed."""
        monkeypatch.delenv("GAZEBO_MCP_SPAWN_ALLOWLIST", raising=False)
        mock = MockBackend()
        r = mock.spawn("ok", "cylinder", 0, 0, 0)
        assert r["ok"] is True

    def test_allowlist_blocks_unknown(self, monkeypatch):
        """Allowlist blocks unlisted types."""
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "box,sphere")
        mock = MockBackend()
        r = mock.spawn("nope", "cylinder", 0, 0, 0)
        assert r["ok"] is False
        assert "not in GAZEBO_MCP_SPAWN_ALLOWLIST" in r["error"]

    def test_allowlist_allows_listed(self, monkeypatch):
        """Allowlist permits listed types."""
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "box,sphere")
        mock = MockBackend()
        r = mock.spawn("yes", "box", 0, 0, 0)
        assert r["ok"] is True

    def test_allowlist_case_insensitive(self, monkeypatch):
        """Allowlist check is case-insensitive."""
        monkeypatch.setenv("GAZEBO_MCP_SPAWN_ALLOWLIST", "BOX,Sphere")
        mock = MockBackend()
        assert mock.spawn("a", "box", 0, 0, 0)["ok"] is True
        assert mock.spawn("b", "sphere", 0, 0, 0)["ok"] is True
        assert mock.spawn("c", "SPHERE", 0, 0, 0)["ok"] is True
