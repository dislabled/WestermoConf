# tests/test_input_validation.py
"""
Unit tests for input validation functions.
These are EASY tests - no network, no external dependencies!
"""
import pytest
from westermo_ser_lib import InputValidator, ValidationError

class TestInputValidator:
    """Test the InputValidator class."""
    
    def test_valid_hostname(self):
        """Test that valid hostnames are accepted."""
        # Test normal hostnames
        assert InputValidator.validate_hostname("test-switch") == "test-switch"
        assert InputValidator.validate_hostname("SWITCH1") == "switch1"  # lowercase
        assert InputValidator.validate_hostname("sw-01-main") == "sw-01-main"
        
    def test_invalid_hostname_empty(self):
        """Test that empty hostnames are rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_hostname("")
            
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_hostname("   ")  # whitespace only
    
    def test_invalid_hostname_too_long(self):
        """Test that overly long hostnames are rejected."""
        long_hostname = "a" * 64  # 64 characters, too long
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_hostname(long_hostname)
    
    def test_invalid_hostname_bad_characters(self):
        """Test that hostnames with invalid characters are rejected."""
        invalid_hostnames = [
            "switch.local",     # dots not allowed
            "switch_01",        # underscores not allowed
            "switch@home",      # special characters not allowed
            "-switch",          # can't start with hyphen
            "switch-",          # can't end with hyphen
        ]
        
        for hostname in invalid_hostnames:
            with pytest.raises(ValidationError, match="Invalid hostname"):
                InputValidator.validate_hostname(hostname)
    
    def test_valid_ip_addresses(self):
        """Test that valid IP addresses are accepted."""
        # Test various valid formats
        ip, cidr = InputValidator.validate_ip_with_cidr("192.168.1.100")
        assert ip == "192.168.1.100"
        assert cidr == "192.168.1.100/24"  # default /24
        
        ip, cidr = InputValidator.validate_ip_with_cidr("10.0.0.1/16")
        assert ip == "10.0.0.1"
        assert cidr == "10.0.0.1/16"
    
    def test_invalid_ip_addresses(self):
        """Test that invalid IP addresses are rejected."""
        invalid_ips = [
            "",                    # empty
            "999.999.999.999",     # out of range
            "192.168.1",           # incomplete
            "192.168.1.1/99",      # invalid CIDR
            "not.an.ip.address",   # not numeric
        ]
        
        for invalid_ip in invalid_ips:
            with pytest.raises(ValidationError):
                InputValidator.validate_ip_with_cidr(invalid_ip)
    
    def test_special_ip_addresses(self):
        """Test handling of special IP addresses."""
        # Loopback should be rejected
        with pytest.raises(ValidationError, match="loopback"):
            InputValidator.validate_ip_with_cidr("127.0.0.1")
        
        # Multicast should be rejected  
        with pytest.raises(ValidationError, match="multicast"):
            InputValidator.validate_ip_with_cidr("224.0.0.1")


