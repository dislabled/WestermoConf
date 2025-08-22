"""
Shared test configuration and fixtures.
"""
import pytest
import logging

@pytest.fixture(autouse=True)
def disable_logging():
    """Disable logging during tests to reduce noise."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)

@pytest.fixture
def sample_device_config():
    """Standard device configuration for tests."""
    return {
        "host": "127.0.0.1",
        "port": 2323,
        "auth_username": "admin", 
        "auth_password": "westermo",
        "platform": "westermo_weos",
        "transport": "telnet"
    }
