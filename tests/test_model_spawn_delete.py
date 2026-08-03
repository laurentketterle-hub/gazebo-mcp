"""Cross-tool state consistency tests for model_spawn / model_delete (fixes #19).

Acceptance: State consistent across tools after spawn/delete mutations.
"""

import pytest
from gazebo_mcp.backend.mock import MockBackend


@pytest.fixture
def backend():
    """Fresh shapes_demo world for each test."""
    b = MockBackend()
    b.seed_demo()
    return b


def _model_names(backend):
    return {m["name"] for m in backend.list_models()}


def _model_count_from_all_tools(backend):
    """Return model counts from every introspection tool."""
    return {
        "list_models": len(backend.list_models()),
        "snapshot": backend.snapshot()["model_count"],
        "world_info": backend.world_info()["model_count"],
        "doctor": backend.doctor()["model_count"],
    }


# SPAWN consistency

def test_spawn_reflected_in_list_models(backend):
    assert "test_box" not in _model_names(backend)
    r = backend.spawn("test_box", "box", 1.0, 2.0, 0.5)
    assert r["ok"] is True
    assert "test_box" in _model_names(backend)


def test_spawn_reflected_in_snapshot(backend):
    before = backend.snapshot()["model_count"]
    backend.spawn("test_sphere", "sphere", 0.0, 0.0, 1.0)
    snap = backend.snapshot()
    assert snap["model_count"] == before + 1
    assert any(m["name"] == "test_sphere" for m in snap["models"])


def test_spawn_reflected_in_world_info(backend):
    before = backend.world_info()["model_count"]
    backend.spawn("wbox", "box", 0.0, 0.0, 0.5)
    assert backend.world_info()["model_count"] == before + 1


def test_spawn_reflected_in_doctor(backend):
    before = backend.doctor()["model_count"]
    backend.spawn("dbox", "box", 0.0, 0.0, 0.5)
    assert backend.doctor()["model_count"] == before + 1


# DELETE consistency

def test_delete_reflected_in_list_models(backend):
    backend.spawn("todel", "box", 0.0, 0.0, 0.5)
    assert "todel" in _model_names(backend)
    r = backend.delete("todel")
    assert r["ok"] is True
    assert "todel" not in _model_names(backend)


def test_delete_reflected_in_snapshot(backend):
    backend.spawn("todel2", "box", 0.0, 0.0, 0.5)
    before = backend.snapshot()["model_count"]
    backend.delete("todel2")
    snap = backend.snapshot()
    assert snap["model_count"] == before - 1
    assert not any(m["name"] == "todel2" for m in snap["models"])


def test_delete_reflected_in_world_info(backend):
    backend.spawn("todel3", "box", 0.0, 0.0, 0.5)
    before = backend.world_info()["model_count"]
    backend.delete("todel3")
    assert backend.world_info()["model_count"] == before - 1


def test_delete_reflected_in_doctor(backend):
    backend.spawn("todel4", "box", 0.0, 0.0, 0.5)
    before = backend.doctor()["model_count"]
    backend.delete("todel4")
    assert backend.doctor()["model_count"] == before - 1


# CROSS-TOOL consistency

def test_all_tools_agree_on_model_count_after_spawn(backend):
    backend.spawn("cross1", "box", 1.0, 2.0, 0.5)
    counts = _model_count_from_all_tools(backend)
    assert len(set(counts.values())) == 1, f"Tools disagree: {counts}"


def test_all_tools_agree_on_model_count_after_delete(backend):
    backend.spawn("cross2", "box", 0.0, 0.0, 0.5)
    backend.delete("cross2")
    counts = _model_count_from_all_tools(backend)
    assert len(set(counts.values())) == 1, f"Tools disagree: {counts}"


def test_all_tools_agree_after_spawn_delete_cycle(backend):
    backend.spawn("cycle_a", "urdf", 0.0, 0.0, 0.1)
    backend.delete("cycle_a")
    backend.spawn("cycle_b", "urdf", 1.0, 1.0, 0.1)
    counts = _model_count_from_all_tools(backend)
    assert len(set(counts.values())) == 1, f"Tools disagree: {counts}"


def test_multiple_spawns_all_tools_consistent(backend):
    for i in range(5):
        backend.spawn(f"bot_{i}", "robot", float(i), 0.0, 0.1)
    counts = _model_count_from_all_tools(backend)
    assert len(set(counts.values())) == 1, f"Tools disagree: {counts}"
    assert counts["list_models"] == 3 + 5


def test_multiple_deletes_all_tools_consistent(backend):
    for i in range(3):
        backend.spawn(f"del_{i}", "box", 0.0, 0.0, 0.5)
    for i in range(3):
        backend.delete(f"del_{i}")
    counts = _model_count_from_all_tools(backend)
    assert len(set(counts.values())) == 1, f"Tools disagree: {counts}"
    assert counts["list_models"] == 3


def test_snapshot_models_match_list_models(backend):
    backend.spawn("snap1", "box", 0.0, 0.0, 0.5)
    backend.spawn("snap2", "sphere", 1.0, 1.0, 0.5)
    list_names = {m["name"] for m in backend.list_models()}
    snap_names = {m["name"] for m in backend.snapshot()["models"]}
    assert list_names == snap_names, f"Mismatch: list={list_names}, snap={snap_names}"


# EDGE CASES

def test_cannot_delete_ground_plane(backend):
    r = backend.delete("ground_plane")
    assert r["ok"] is False
    assert "cannot delete" in r["error"].lower()


def test_cannot_spawn_duplicate(backend):
    backend.spawn("dup", "box", 0.0, 0.0, 0.5)
    r = backend.spawn("dup", "box", 1.0, 1.0, 0.5)
    assert r["ok"] is False
    assert "already exists" in r["error"].lower()


def test_cannot_delete_nonexistent(backend):
    r = backend.delete("ghost")
    assert r["ok"] is False
    assert "unknown" in r["error"].lower()


def test_spawned_model_has_correct_pose(backend):
    backend.spawn("posed", "cylinder", 3.0, 4.0, 0.75, yaw=1.57)
    m = backend.get_pose("posed")
    assert m["ok"] is True
    assert m["pose"]["x"] == 3.0
    assert m["pose"]["y"] == 4.0
    assert m["pose"]["z"] == 0.75
    assert m["pose"]["yaw"] == 1.57


def test_spawned_model_appears_in_get_pose(backend):
    backend.spawn("gp", "box", 5.0, 5.0, 2.0)
    p = backend.get_pose("gp")
    assert p["ok"] is True
    assert p["name"] == "gp"


def test_deleted_model_removed_from_get_pose(backend):
    backend.spawn("gd", "box", 0.0, 0.0, 0.5)
    backend.delete("gd")
    p = backend.get_pose("gd")
    assert p["ok"] is False
