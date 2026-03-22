"""Shared test fixtures."""

import pytest


@pytest.fixture
def mock_settings():
    """Provide mock engine settings for tests."""
    return {
        "port": 48765,
        "host": "127.0.0.1",
        "log_level": "debug",
    }
