#!/usr/bin/python3
"""
Westermo_lib.

This module uses a ssh connection to communicate with Westermo,
currently only testet on the lynx range for common configuring.
"""
from typing import Any, Tuple
import re
import logging
from time import sleep
from ipaddress import ip_address, ip_network, AddressValueError
from threading import Thread
from scrapli import Scrapli  # type: ignore
from telnet2serlib import Handler  # type: ignore


# Custom exceptions for better error handling
class WestermoError(Exception):
    """Base exception for Westermo operations."""

    pass


class NetworkError(WestermoError):
    """Network communication errors."""

    pass


class ValidationError(WestermoError):
    """Input validation errors."""

    pass


class ParseError(WestermoError):
    """Data parsing errors."""

    pass


class ConfigurationError(WestermoError):
    """Device configuration errors."""

    pass


# Enhanced logging configuration
def setup_logging():
    """Set up consistent logging configuration."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


logger = setup_logging()


class InputValidator:
    """Input validation utilities for Westermo devices."""

    HOSTNAME_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$")

    @staticmethod
    def validate_hostname(hostname: str) -> str:
        """Validate and sanitize hostname.

        Args:
            hostname (str): Hostname string to validate

        Returns:
            str: Sanitized hostname

        Raises:
            ValidationError: If hostname is invalid
        """
        if not hostname or not hostname.strip():
            raise ValidationError("Hostname cannot be empty")

        hostname = hostname.strip()

        if len(hostname) > 63:
            raise ValidationError("Hostname too long (max 63 characters)")

        if not InputValidator.HOSTNAME_PATTERN.match(hostname):
            raise ValidationError("Invalid hostname format. Use only letters, numbers, and hyphens.")

        return hostname.lower()

    @staticmethod
    def validate_ip_with_cidr(ip_str: str) -> Tuple[str, str]:
        """Validate IP address and return with CIDR notation.

        Args:
            ip_str (str): IP address string (with or without CIDR)

        Returns:
            Tuple[str, str]: (ip_address, network_with_cidr)

        Raises:
            ValidationError: If IP address is invalid
        """
        if not ip_str or not ip_str.strip():
            raise ValidationError("IP address cannot be empty")

        ip_str = ip_str.strip()

        try:
            if "/" in ip_str:
                ip_part, cidr_part = ip_str.split("/", 1)
                cidr = int(cidr_part)
                if not 0 <= cidr <= 32:
                    raise ValidationError("CIDR must be between 0 and 32")
            else:
                ip_part = ip_str
                cidr = 24

            validated_ip = ip_address(ip_part)

            if validated_ip.is_loopback:
                raise ValidationError("Cannot use loopback address")
            if validated_ip.is_multicast:
                raise ValidationError("Cannot use multicast address")

            return str(validated_ip), f"{validated_ip}/{cidr}"

        except (ValueError, AddressValueError) as e:
            raise ValidationError(f"Invalid IP address: {str(e)}")


def threaded(func):
    """
    Decorate function for multithreading.

    Decorator that multithreads the target function
    with the given parameters. Returns the thread
    created for the function.
    """

    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

    return wrapper


def str_to_dict(string):
    """Parse a string to a dictionary."""
    string = string.strip("{}")
    pairs = string.split(", ")
    return {key[1:-2]: str(value) for key, value in (pair.split(": ") for pair in pairs)}


class Westermo:
    """Class for interacting with the westermo switch."""

    def __init__(self, **kwargs) -> None:
        """Initialize the Class."""
        from config import Config

        device_config = Config.get_device_config()
        device_config.update(kwargs)

        safe_params = {k: v for k, v in kwargs.items() if k not in ["auth_password", "password"]}
        logger.info("Initializing Westermo connection: %s", safe_params)

        self.DEVICE = device_config

        # Only start telnet2serial bridge if we're using telnet transport
        if kwargs.get("transport") == "telnet" and kwargs.get("port") == 2323:
            logger.info("Starting telnet-to-serial bridge...")
            self.telnet2serlib()
            sleep(0.2)
        else:
            logger.info("Direct connection mode - skipping telnet-to-serial bridge")

    def __enter__(self):
        """Run commands on class enter."""
        logger.info("Establishing connection to Westermo device")
        try:
            self.conn = Scrapli(**self.DEVICE)
            logger.debug("Scrapli initialized")
            self.conn.open()
            logger.info("Scrapli connection opened")
            self.set_interactive()
            return self
        except Exception as e:
            logger.error("Failed to connect: %s", str(e))
            raise NetworkError(f"Connection failed: {str(e)}")

    def __exit__(self, *args) -> None:
        """Run commands on class exit."""
        _ = args
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.close()
                logger.info("Disconnected from Westermo device")
            except Exception as e:
                logger.warning("Error during disconnect: %s", str(e))

    def _validate_connection(self) -> None:
        """Validate that connection is established before operations."""
        if not hasattr(self, "conn") or self.conn is None:
            raise NetworkError("Not connected to device. Use 'with Westermo(...):' context manager.")

    @threaded
    def telnet2serlib(self):
        """Start the telnet to serial shim."""

        from config import Config
        try:
            connections = Handler(
                tel_port=Config.TELNET_PORT,
                ser_port=Config.SERIAL_PORT,
                baud=Config.SERIAL_BAUD,
                timeout=Config.SERIAL_TIMEOUT,
                xonxoff=Config.SERIAL_XONXOFF
            )
            while True:
                connections.run()
        except Exception as e:
            logger.error("Telnet bridge error: %s", str(e))
            logger.warning("Continuing without telnet bridge...")

    def get_uptime(self) -> str:
        """Get the uptime of the switch.

        Returns:
            str: Device uptime string

        Raises:
            NetworkError: If unable to retrieve uptime
        """
        self._validate_connection()

        try:
            uptime = self.conn.send_command("uptime")

            if uptime.failed:
                logger.error("Failed to get uptime: %s", uptime.result)
                raise NetworkError("Unable to retrieve uptime")

            uptime_result = uptime.result.strip()
            if " " in uptime_result:
                uptime_value = uptime_result.split(" ")[0]  # Get first part before space
            else:
                uptime_value = uptime_result[:8]  # Fallback to first 8 chars

            logger.debug("uptime: %s", uptime_value)
            return uptime_value

        except NetworkError:
            raise
        except Exception as e:
            logger.error("Unexpected error getting uptime: %s", str(e))
            raise NetworkError(f"Uptime retrieval failed: {str(e)}")

    def get_sysinfo(self) -> dict:
        """Get system info and return it as a list|dict.

        Returns:
            dict: System parameters dictionary

        Raises:
            NetworkError: If unable to communicate with device
            ParseError: If unable to parse device response
        """
        self._validate_connection()

        try:
            sysinfo = self.conn.send_command("show system-information")

            if sysinfo.failed:
                raise NetworkError(f"Command failed: {sysinfo.result}")

            return_values: Any = list(sysinfo.ttp_parse_output(template="ttp_templates/system-information.txt"))

            if not return_values or not return_values[0]:
                raise ParseError("Failed to parse system information output")

            system_info = return_values[0]
            logger.debug("get_sysinfo function: %s", system_info)
            return system_info

        except (NetworkError, ParseError):
            raise
        except Exception as e:
            logger.error("Failed to get system info: %s", str(e))

    def get_mgmt_ip(self) -> list[dict]:
        """Get current management ip info.

        Returns:
            list[dict]: Management interface information

        Raises:
            NetworkError: If unable to retrieve interface information
            ParseError: If unable to parse response
        """
        self._validate_connection()

        try:
            ip_mgmt_info = self.conn.send_command("show ifaces")

            if ip_mgmt_info.failed:
                raise NetworkError(f"Command failed: {ip_mgmt_info.result}")

            return_values: Any = list(ip_mgmt_info.ttp_parse_output(template="ttp_templates/show_ifaces.txt"))

            if not return_values or not return_values[0]:
                raise ParseError("Failed to parse interface information")

            logger.debug("get_mgmt_ip function: %s", return_values[0])
            return return_values[0]

        except (NetworkError, ParseError):
            raise
        except Exception as e:
            logger.error("Error getting management IP: %s", str(e))
            raise NetworkError(f"Management IP retrieval failed: {str(e)}")

    def get_ports(self) -> list[dict]:
        """Get status of ports, and return it as a list|dict.

        Returns:
            list[dict]: Status of all ports

        Raises:
            NetworkError: If unable to retrieve port information
            ParseError: If unable to parse port data
        """
        self._validate_connection()

        try:
            status_ports = self.conn.send_command("show port")

            if status_ports.failed:
                raise NetworkError(f"Command failed: {status_ports.result}")

            first_parse: Any = list(status_ports.ttp_parse_output(template="ttp_templates/ports.txt"))

            if not first_parse or len(first_parse[0]) < 3:
                raise ParseError("Failed to parse port information or no ports found")

            return_values = first_parse[0][2:]

            for keys in return_values:
                try:
                    keys["port"] = int(keys["port"][4:])  # Remove "Eth " prefix
                    keys["vid"] = int(keys["vid"])
                    keys["link"] = keys["link"] == "UP"

                    alarm_status = keys.get("alarm", "N/A")
                    if alarm_status == "ALARM":
                        keys["alarm"] = True
                    elif alarm_status == "None":
                        keys["alarm"] = False
                    else:
                        keys["alarm"] = False

                except (ValueError, KeyError) as e:
                    logger.warning("Error processing port data: %s", str(e))

            logger.debug("get_ports function: %s", return_values)
            return return_values

        except (NetworkError, ParseError):
            raise
        except Exception as e:
            logger.error("Error getting port status: %s", str(e))
            raise NetworkError(f"Port status retrieval failed: {str(e)}")

    def get_frnt(self) -> list | dict:
        """Get status of ports, and returns it as a list|dict.

        Returns:
            list|dict: Status of all ports

        Raises:
            NetworkError: If unable to retrieve FRNT information
        """
        self._validate_connection()

        try:
            status_ports = self.conn.send_command("show frnt")

            if status_ports.failed:
                raise NetworkError(f"Command failed: {status_ports.result}")

            return_values: Any = list(status_ports.ttp_parse_output(template="ttp_templates/show_frnt.txt"))[0]
            logger.debug("get_frnt function: %s", status_ports.result)
            return return_values

        except NetworkError:
            raise
        except Exception as e:
            logger.error("Error getting FRNT status: %s", str(e))
            raise NetworkError(f"FRNT status retrieval failed: {str(e)}")

    def set_frtn(self, ports: tuple = (1, 2)) -> None:
        """Toggle the FRNT Ring.

        Args:
            ports (tuple): Ports to configure for FRNT ring

        Raises:
            ValidationError: If port configuration is invalid
            NetworkError: If configuration fails
        """
        self._validate_connection()

        try:
            if ports == (0,):  # Note: should be (0,) not (0)
                result = self.conn.send_config("no frnt 1")
                if result.failed:
                    raise ConfigurationError(f"Failed to disable FRNT: {result.result}")
                logger.debug("set_frnt function: disabling frnt")
            else:
                # Validate ports
                if not ports or len(ports) > 2:
                    raise ValidationError("FRNT requires exactly 1 or 2 ports")

                for port in ports:
                    if not isinstance(port, int) or port < 1 or port > 48:
                        raise ValidationError(f"Invalid port number: {port}")

                portstr = ",".join(str(x) for x in ports)
                result = self.conn.send_config(f"frnt 1 ring-ports {portstr}")
                if result.failed:
                    raise ConfigurationError(f"Failed to set FRNT ports: {result.result}")
                logger.debug("set_frnt function: frnt set on port %s", portstr)

        except (ValidationError, ConfigurationError):
            raise
        except Exception as e:
            logger.error("Error configuring FRNT: %s", str(e))
            raise NetworkError(f"FRNT configuration failed: {str(e)}")

    def set_focal(self, member: bool = True) -> None:
        """Set member on the FRNT Ring.

        Args:
            member (bool): True for member mode, False for focal point

        Raises:
            NetworkError: If configuration fails
        """
        self._validate_connection()

        try:
            if member:
                result = self.conn.send_config("frnt 1 no focal-point")
                if result.failed:
                    raise ConfigurationError(f"Failed to set member mode: {result.result}")
                logger.debug("set_focal function: member")
            else:
                result = self.conn.send_config("frnt 1 focal-point")
                if result.failed:
                    raise ConfigurationError(f"Failed to set focal point: {result.result}")
                logger.debug("set_focal function: master")

        except ConfigurationError:
            raise
        except Exception as e:
            logger.error("Error setting focal mode: %s", str(e))
            raise NetworkError(f"Focal configuration failed: {str(e)}")

    def set_alarm(self, alarm: list[bool]) -> None:
        """Configure alarm when link down for interfaces in list.

        Args:
            alarm (list): interfaces with alarm on or off

        Raises:
            ValidationError: If alarm list is invalid
            NetworkError: If configuration fails
        """
        self._validate_connection()

        if len(alarm) > 48:  # Most switches have max 48 ports
            raise ValidationError("Too many ports specified (max 48)")

        if not alarm:  # Empty list
            logger.info("No alarm configuration provided")
            return

        enabled_ports = [str(i + 1) for i, enabled in enumerate(alarm) if enabled]
        port_list = ",".join(enabled_ports)

        logger.info("Configuring alarms for ports: %s", port_list or "none")

        try:
            clear_commands = ["alarm no action 1", "alarm no trigger 1"]

            for cmd in clear_commands:
                result = self.conn.send_config(cmd)
                if result.failed:
                    logger.warning("Failed to clear alarm config: %s", result.result)

            if port_list:
                alarm_commands = [
                    f"alarm trigger 1 link-alarm condition low port {port_list}",
                    "alarm action 1 target led,log,digout",
                ]

                for cmd in alarm_commands:
                    result = self.conn.send_config(cmd)
                    if result.failed:
                        raise ConfigurationError(f"Alarm configuration failed: {result.result}")

            logger.debug("set_alarm function: set alarm on ifaces %s ON", port_list)

        except (ValidationError, ConfigurationError):
            raise
        except Exception as e:
            logger.error("Error configuring alarms: %s", str(e))
            raise NetworkError(f"Alarm configuration failed: {str(e)}")

    def set_mgmt_ip(self, ip_add: str) -> bool:
        """Change the management ip-address of the switch to (ip).

        Args:
            ip_add (str): IP Address to set

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValidationError: If IP address format is invalid
        """
        self._validate_connection()

        try:
            validated_ip, ip_with_cidr = InputValidator.validate_ip_with_cidr(ip_add)

            logger.debug("set_mgmt_ip function: setting vlan1 to static 192.168.2.200/24")
            result = self.conn.send_config("iface vlan1 inet static address 192.168.2.200/24")
            if result.failed:
                logger.error("Failed to set primary IP: %s", result.result)
                return False

            self.conn.send_config("exit")

            logger.debug("set_mgmt_ip function: removing all secondary ip")
            interactive_result = self.conn.send_interactive(
                [
                    (
                        "iface vlan1 inet static no address secondary",
                        "Remove all secondary IP addresses, are you sure (y/N)? ",
                        False,
                    ),
                    ("y", "", False),
                ],
                privilege_level="configuration",
            )

            if interactive_result.failed:
                logger.error("Failed to remove secondary IPs: %s", interactive_result.result)
                return False

            self.conn.send_config("exit")

            logger.debug("set_mgmt_ip function: setting vlan1 secondary to %s", ip_with_cidr)
            result = self.conn.send_config(f"iface vlan1 inet static address {ip_with_cidr} secondary")
            if result.failed:
                logger.error("Failed to set secondary IP: %s", result.result)
                return False

            return True

        except ValidationError as e:
            logger.warning("IP address validation failed: %s", str(e))
            raise
        except Exception as e:
            logger.error("Error setting management IP: %s", str(e))
            return False

    def set_hostname(self, hostname: str) -> None:
        """Change the hostname of the switch.

        Args:
            hostname (str): Hostname to switch to

        Raises:
            ValidationError: If hostname is invalid
            NetworkError: If configuration fails
        """
        self._validate_connection()

        try:
            validated_hostname = InputValidator.validate_hostname(hostname)

            result = self.conn.send_config(f"system hostname {validated_hostname}")
            if result.failed:
                raise ConfigurationError(f"Failed to set hostname: {result.result}")

            logger.debug("conf_hostname function: set %s", validated_hostname)

        except ValidationError as e:
            logger.warning("Hostname validation failed: %s", str(e))
            raise
        except ConfigurationError:
            raise
        except Exception as e:
            logger.error("Error setting hostname: %s", str(e))
            raise NetworkError(f"Hostname configuration failed: {str(e)}")

    def set_interactive(self, interactive: bool = True) -> None:
        """Set the interactive mode on the switch.

        This enables paging, but also lets you structure commands fully

        Args:
            interactive (bool): True for interactive mode, False for batch mode
        """
        self._validate_connection()

        try:
            if interactive:
                result = self.conn.send_command("interactive")
                if result.failed:
                    logger.warning("Failed to set interactive mode: %s", result.result)
                else:
                    logger.debug("Interactive mode set")
            else:
                result = self.conn.send_command("batch")
                if result.failed:
                    logger.warning("Failed to set batch mode: %s", result.result)
                else:
                    logger.debug("Batch mode set")
        except Exception as e:
            logger.warning("Error setting interactive mode: %s", str(e))

    def set_location(self, location: str) -> None:
        """Change the location parameter of the switch.

        Args:
            location (str): location string to switch to

        Raises:
            ValidationError: If location format is invalid
            NetworkError: If configuration fails
        """
        self._validate_connection()

        try:
            if location == "":
                result = self.conn.send_config("no system location")
                if result.failed:
                    raise ConfigurationError(f"Failed to remove location: {result.result}")
                logger.debug("set_location function: removing location")
            else:
                if len(location) > 255:
                    raise ValidationError("Location too long (max 255 characters)")

                location = re.sub("[^a-zA-Z0-9 \n\\.]", "", location)
                result = self.conn.send_config(f"system location '{location}'")
                if result.failed:
                    raise ConfigurationError(f"Failed to set location: {result.result}")
                logger.debug("set_location function: set to: %s", location)

        except (ValidationError, ConfigurationError):
            raise
        except Exception as e:
            logger.error("Error setting location: %s", str(e))
            raise NetworkError(f"Location configuration failed: {str(e)}")

    def factory_conf(self) -> None:
        """Reset device to factory defaults.

        Raises:
            NetworkError: If factory reset fails
        """
        self._validate_connection()

        try:
            logger.warning("Initiating factory reset - this will erase all configuration")

            result = self.conn.send_interactive([("factory-reset", "=> Are you sure (y/N)?", False), ("y", "", False)])

            if result.failed:
                raise ConfigurationError(f"Factory reset failed: {result.result}")

            logger.critical("factory_conf function: Factory defaults set")

        except ConfigurationError:
            raise
        except Exception as e:
            logger.error("Error during factory reset: %s", str(e))
            raise NetworkError(f"Factory reset failed: {str(e)}")

    def save_run2startup(self) -> bool:
        """Save the configuration from running to startup.

        Returns:
            bool: True if successful, False otherwise
        """
        self._validate_connection()

        try:
            response = self.conn.send_command("copy run start")
            logger.debug("save_run2startup function: %s", response.result)

            if response.failed or response.result != "":
                logger.error("Failed to save configuration: %s", response.result)
                return False

            logger.info("Configuration saved successfully")
            return True

        except Exception as e:
            logger.error("Error saving configuration: %s", str(e))
            return False


def save_config(self) -> str:
    """Get the startup config and returns it as a decoded string.

    Returns:
        str: config string

    Raises:
        NetworkError: If unable to retrieve configuration
    """
    self._validate_connection()

    try:
        self.set_interactive(False)
        result = self.conn.send_command("show startup-config")

        if result.failed:
            raise NetworkError(f"Failed to retrieve startup config: {result.result}")

        config = result.result
        self.set_interactive(True)
        logger.debug("Successfully retrieved startup configuration")
        return config

    except NetworkError:
        self.set_interactive(True)
        raise
    except Exception as e:
        logger.error("Error retrieving config: %s", str(e))
        self.set_interactive(True)
        raise NetworkError(f"Configuration retrieval failed: {str(e)}")

    def compare_config(self) -> bool:
        """Compare the running and startup config and returns status.

        Returns:
            bool: True = Match, False = Mismatch

        Raises:
            NetworkError: If unable to retrieve configurations
        """
        self._validate_connection()

        try:
            self.set_interactive(False)

            startup_result = self.conn.send_command("show startup-config")
            if startup_result.failed:
                raise NetworkError(f"Failed to get startup config: {startup_result.result}")

            running_result = self.conn.send_command("show running-config")
            if running_result.failed:
                raise NetworkError(f"Failed to get running config: {running_result.result}")

            # Process startup config (remove footer)
            raw_startup = startup_result.result
            parsed_startup = "".join(raw_startup.splitlines(keepends=True)[:-4]).rstrip()
            raw_running = running_result.result

            self.set_interactive(True)

            configs_match = parsed_startup == raw_running
            logger.debug("compare_config function: %s", configs_match)
            return configs_match

        except NetworkError:
            self.set_interactive(True)
            raise
        except Exception as e:
            logger.error("Error comparing configurations: %s", str(e))
            self.set_interactive(True)
            raise NetworkError(f"Configuration comparison failed: {str(e)}")

    def get_alarm_log(self) -> list | dict:
        """Return the alarm log as a list | dict.

        Returns:
            list|dict: eventlog

        Raises:
            NetworkError: If unable to retrieve alarm log
        """
        self._validate_connection()

        try:
            logger.debug("get_alarm_log function: ")
            returnobj = self.conn.send_command("show alarm")

            if returnobj.failed:
                raise NetworkError(f"Command failed: {returnobj.result}")

            return_values: Any = list(returnobj.ttp_parse_output(template="ttp_templates/alarm_log.txt"))[0]
            logger.debug(return_values)
            return return_values

        except NetworkError:
            raise
        except Exception as e:
            logger.error("Error getting alarm log: %s", str(e))
            raise NetworkError(f"Alarm log retrieval failed: {str(e)}")

    def get_event_log(self) -> str:
        """Return the event list as a list | dict.

        Returns:
            str: log
        """
        self._validate_connection()

        try:
            logger.debug("get_event_log function: ")
            self.set_interactive(False)
            return_values = self.conn.send_command("alarm log").result
            self.set_interactive(True)
            logger.debug(return_values)
            return return_values
        except Exception as e:
            logger.error("Error getting event log: %s", str(e))
            self.set_interactive(True)
            return ""


if __name__ == "__main__":
    SWITCH = {
        "host": "127.0.0.1",
        "port": 2323,
        "auth_username": "admin",
        "auth_password": "westermo",
        "platform": "westermo_weos",
        "transport": "telnet",
    }

    try:
        with Westermo(**SWITCH) as switch:
            switch.set_interactive()
            switch.get_sysinfo()
            switch.get_uptime()
            input()
    except WestermoError as e:
        logger.error("Westermo operation failed: %s", str(e))
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
