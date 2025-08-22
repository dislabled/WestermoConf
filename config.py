# config.py - Configuration file
"""
Simple configuration for Westermo Configurator.
"""
import os
from pathlib import Path


class Config:
    """Application configuration."""

    # === DEVICE CONNECTION SETTINGS ===
    DEFAULT_DEVICE = {
        "host": "127.0.0.1",
        "port": 2323,
        "auth_username": "admin",
        "auth_password": "westermo",
        "transport": "telnet",
        "platform": "westermo_weos",
    }

    # Connection timeouts and retries
    CONNECTION_TIMEOUT = 30
    COMMAND_TIMEOUT = 10
    MAX_RETRIES = 3

    # === TELNET TO SERIAL SETTINGS ===
    TELNET_PORT = 2323
    SERIAL_PORT = "/dev/ttyUSB0"
    SERIAL_BAUD = 115200
    SERIAL_TIMEOUT = 1
    SERIAL_XONXOFF = True

    # === GUI SETTINGS ===
    WINDOW_TITLE = "Westermo Configurator"
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    AUTO_REFRESH_SECONDS = 30

    # === FILE PATHS ===
    CSV_DIRECTORY = "./site/"
    CONFIG_DIRECTORY = "./site/configs/"
    LOG_DIRECTORY = "./logs/"

    # === LOGGING SETTINGS ===
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE = True
    LOG_TO_CONSOLE = True
    MAX_LOG_SIZE_MB = 10
    LOG_BACKUP_COUNT = 5

    @classmethod
    def ensure_directories(cls):
        """Create directories if they don't exist."""
        dirs = [cls.CSV_DIRECTORY, cls.CONFIG_DIRECTORY, cls.LOG_DIRECTORY]
        for directory in dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_device_config(cls, host=None):
        """Get device configuration with optional host override."""
        config = cls.DEFAULT_DEVICE.copy()
        if host:
            config["host"] = host
        return config

    @classmethod
    def check_serial_device(cls):
        """Check if the serial device exists and is accessible."""
        if not os.path.exists(cls.SERIAL_PORT):
            return False, f"Device {cls.SERIAL_PORT} does not exist"
        
        if not os.access(cls.SERIAL_PORT, os.R_OK | os.W_OK):
            return False, f"No permission to access {cls.SERIAL_PORT}"
        
        return True, "Serial device OK"

    @classmethod
    def get_available_serial_ports(cls):
        """Get list of available serial ports."""
        import glob
        import os
        
        # Common serial port patterns
        patterns = [
            '/dev/ttyUSB*',  # USB-to-serial adapters on Linux
            '/dev/ttyACM*',  # Arduino/CDC devices on Linux
            '/dev/cu.usbserial*',  # macOS USB serial
        ]
        
        ports = []
        for pattern in patterns:
            ports.extend(glob.glob(pattern))
        
        # Filter to only accessible ports
        accessible_ports = []
        for port in ports:
            if os.access(port, os.R_OK | os.W_OK):
                accessible_ports.append(port)
        
        return accessible_ports

    @classmethod
    def load_from_env(cls):
        """Override settings from environment variables."""
        cls.DEFAULT_DEVICE["host"] = os.getenv("WESTERMO_HOST", cls.DEFAULT_DEVICE["host"])
        cls.DEFAULT_DEVICE["auth_username"] = os.getenv("WESTERMO_USERNAME", cls.DEFAULT_DEVICE["auth_username"])
        cls.DEFAULT_DEVICE["auth_password"] = os.getenv("WESTERMO_PASSWORD", cls.DEFAULT_DEVICE["auth_password"])

        cls.LOG_LEVEL = os.getenv("WESTERMO_LOG_LEVEL", cls.LOG_LEVEL)
        cls.CSV_DIRECTORY = os.getenv("WESTERMO_CSV_DIR", cls.CSV_DIRECTORY)

        cls.ensure_directories()


# Initialize configuration when imported
Config.load_from_env()
