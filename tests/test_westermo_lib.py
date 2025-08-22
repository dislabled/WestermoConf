"""
Tests for Westermo device operations.
These tests use MOCKING - we fake the network operations!
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from westermo_ser_lib import Westermo, NetworkError, ValidationError, ConfigurationError, ParseError


class TestWestermoDevice:
    """Test Westermo device operations."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock Scrapli connection for testing."""
        mock_conn = Mock()
        mock_conn.send_command = Mock()
        mock_conn.send_config = Mock()
        mock_conn.send_interactive = Mock()
        return mock_conn

    @pytest.fixture
    def westermo_device(self, mock_connection):
        """Create a Westermo device with mocked connection."""
        device = Westermo(
            host="127.0.0.1",
            port=2323,
            auth_username="admin",
            auth_password="westermo",
            platform="westermo_weos",
            transport="telnet",
        )
        device.conn = mock_connection
        return device

    def test_get_uptime_success(self, westermo_device, mock_connection):
        """Test successful uptime retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.result = "12:34:56 up 5 days"
        mock_response.failed = False
        mock_connection.send_command.return_value = mock_response

        # Call the method
        uptime = westermo_device.get_uptime()

        # Verify the result - should be just the time part
        assert uptime == "12:34:56"
        mock_connection.send_command.assert_called_once_with("uptime")

    def test_set_hostname_config_failure(self, westermo_device, mock_connection):
        """Test hostname setting when device configuration fails."""
        # Setup mock to simulate configuration failure
        mock_response = Mock()
        mock_response.failed = True
        mock_response.result = "Invalid command"
        mock_connection.send_config.return_value = mock_response

        # Call the method and expect ConfigurationError (not NetworkError)
        with pytest.raises(ConfigurationError, match="Failed to set hostname"):
            westermo_device.set_hostname("valid-hostname")

    def test_get_system_info_parse_failure(self, westermo_device, mock_connection):
        """Test system info retrieval when parsing fails."""
        # Setup mock response with empty parsed data
        mock_response = Mock()
        mock_response.failed = False
        mock_response.ttp_parse_output.return_value = []  # Empty result
        mock_connection.send_command.return_value = mock_response

        # Call the method and expect parse error
        with pytest.raises(ParseError, match="Failed to parse"):
            westermo_device.get_sysinfo()  # Note: method name should be get_sysinfo not get_system_info

    # Add test for edge cases in uptime parsing
    def test_get_uptime_different_formats(self, westermo_device, mock_connection):
        """Test uptime parsing with different input formats."""
        test_cases = [
            ("12:34:56 up 5 days", "12:34:56"),
            ("09:15:23", "09:15:23"),  # No extra text
            ("23:59:59 up 1 day, 2:34", "23:59:59"),
        ]

        for input_str, expected in test_cases:
            mock_response = Mock()
            mock_response.result = input_str
            mock_response.failed = False
            mock_connection.send_command.return_value = mock_response

            uptime = westermo_device.get_uptime()
            assert uptime == expected, f"Failed for input: {input_str}"
