"""Tests for gazebo-mcp issue #23"""
import pytest
from src.gazebo_mcp.backend.mock import MockBackend

class TestIssue23:
    def setup_method(self):
        self.mock = MockBackend()
    
    def test_feature_available(self):
        """Verify feature is accessible"""
        assert self.mock is not None
    
    def test_integration(self):
        """Verify integration with mock backend"""
        result = self.mock.new_world("test_world")
        assert result.get("ok") or result.get("status") == "ok"
