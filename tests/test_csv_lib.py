"""
Tests for CSV handling functionality.
"""

import pytest
import tempfile
import os
from csv_lib import ConfigFile


class TestConfigFile:
    """Test CSV file operations."""

    @pytest.fixture
    def sample_csv_file(self):
        """Create a temporary CSV file for testing."""
        content = """Cabinet,AP,SW,IOG,MBB,DIPB,MBR,DIPR,IBC IP address,Switch IP address,Position,MAC M,MAC R
CAB01,1,1,0,1,1,1,0,192.168.1.10,192.168.1.100,Building A Room 1,,
CAB02,1,1,0,1,0,0,1,192.168.1.11,192.168.1.101,Building A Room 2,aa:bb:cc:dd:ee:ff,
CAB03,1,0,0,0,0,0,0,192.168.1.12,192.168.1.102,Building B Room 1,,"""

        # Create temporary file
        fd, path = tempfile.mkstemp(suffix=".csv", text=True)
        try:
            with os.fdopen(fd, "w") as tmp_file:
                tmp_file.write(content)
            yield path
        finally:
            os.unlink(path)

    def test_read_config_valid_file(self, sample_csv_file):
        """Test reading a valid CSV configuration file."""
        config_file = ConfigFile()
        result = config_file.read_config(sample_csv_file)

        # Check that we got the expected number of rows
        assert len(result) == 3

        # Check first row content
        first_row = result[0]
        assert first_row["Cabinet"] == "CAB01"
        assert first_row["SW"] == "1"
        assert first_row["Switch IP address"] == "192.168.1.100"

    def test_read_config_nonexistent_file(self):
        """Test handling of nonexistent files."""
        config_file = ConfigFile()
        with pytest.raises(FileNotFoundError):
            config_file.read_config("nonexistent_file.csv")

    def test_write_config_main_mac(self, sample_csv_file):
        """Test writing MAC address to main column."""
        config_file = ConfigFile()

        # Write MAC address for CAB01
        config_file.write_config(sample_csv_file, "CAB01", "11:22:33:44:55:66", main=True)

        # Read back and verify
        result = config_file.read_config(sample_csv_file)
        cab01_row = next(row for row in result if row["Cabinet"] == "CAB01")
        assert cab01_row["MAC M"] == "11:22:33:44:55:66"

    def test_write_config_reserve_mac(self, sample_csv_file):
        """Test writing MAC address to reserve column."""
        config_file = ConfigFile()

        # Write MAC address for CAB02 reserve
        config_file.write_config(sample_csv_file, "CAB02", "aa:bb:cc:dd:ee:99", main=False)

        # Read back and verify
        result = config_file.read_config(sample_csv_file)
        cab02_row = next(row for row in result if row["Cabinet"] == "CAB02")
        assert cab02_row["MAC R"] == "aa:bb:cc:dd:ee:99"
