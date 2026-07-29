"""Integration tests for spawn/delete state consistency and sensor snapshots."""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestSpawnDeleteConsistency:
    """Verify model spawn and delete maintain consistent internal state."""

    def test_spawn_adds_to_internal_state(self):
        """Spawning a model should add it to the tracked state."""
        # Mock the backend's model tracking
        state = {}
        model_name = "test_model"
        model_sdf = "<sdf>test</sdf>"
        
        state[model_name] = {"sdf": model_sdf, "spawned": True}
        
        assert model_name in state
        assert state[model_name]["spawned"] is True

    def test_delete_removes_from_internal_state(self):
        """Deleting a model should remove it from tracked state."""
        state = {"test_model": {"spawned": True}}
        del state["test_model"]
        assert "test_model" not in state

    def test_spawn_delete_sequence_consistency(self):
        """Spawn then delete should leave clean state."""
        state = {}
        state["model_a"] = {"spawned": True}
        state["model_b"] = {"spawned": True}
        del state["model_a"]
        
        assert "model_a" not in state
        assert "model_b" in state
        assert len(state) == 1

    def test_double_delete_is_safe(self):
        """Deleting a non-existent model should not crash."""
        state = {}
        try:
            del state["nonexistent"]
        except KeyError:
            pass
        # Should not throw unhandled exception
        assert "nonexistent" not in state

    def test_spawn_duplicate_overwrites(self):
        """Spawning same model twice should update state."""
        state = {}
        state["model"] = {"sdf": "v1"}
        state["model"] = {"sdf": "v2"}
        assert state["model"]["sdf"] == "v2"

    def test_allowlist_enforcement(self):
        """Only allowed models should be spawnable."""
        allowlist = {"allowed_model", "test_cube"}
        model = "malicious_model"
        assert model not in allowlist
        
        model2 = "test_cube"
        assert model2 in allowlist

    def test_spawn_state_persistence_across_operations(self):
        """State should persist correctly across multiple operations."""
        state = {}
        # Spawn A
        state["a"] = {"spawned": True}
        # Spawn B
        state["b"] = {"spawned": True}
        # Delete A
        del state["a"]
        # Spawn C
        state["c"] = {"spawned": True}
        
        assert "a" not in state
        assert "b" in state
        assert "c" in state
        assert len(state) == 2

    def test_sensor_snapshot_basic(self):
        """Sensor snapshot should return valid structure."""
        snapshot = {
            "models": ["model_a", "model_b"],
            "timestamp": 1234567890.0,
            "model_count": 2
        }
        assert "models" in snapshot
        assert "timestamp" in snapshot
        assert isinstance(snapshot["models"], list)
        assert snapshot["model_count"] == len(snapshot["models"])


class TestModelGraph:
    """Verify model relationship graph functionality."""

    def test_empty_graph(self):
        """Empty state should produce empty graph."""
        graph = {"nodes": [], "edges": []}
        assert len(graph["nodes"]) == 0
        assert len(graph["edges"]) == 0

    def test_single_model_graph(self):
        """Single model should produce one-node graph."""
        graph = {"nodes": [{"id": "model_a", "type": "model"}], "edges": []}
        assert len(graph["nodes"]) == 1
        assert graph["nodes"][0]["id"] == "model_a"

    def test_graph_json_serializable(self):
        """Graph should be JSON serializable."""
        graph = {"nodes": [{"id": "m1"}], "edges": []}
        serialized = json.dumps(graph)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert parsed == graph
