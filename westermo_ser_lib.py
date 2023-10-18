#!/usr/bin/python3
"""
Westermo_lib.

This module uses a ssh connection to communicate with Westermo,
currently only testet on the lynx range for common configuring.
"""
from typing import Any
import re
import logging
from time import sleep
from ipaddress import ip_address
from threading import Thread
from scrapli import Scrapli  # type: ignore
from telnet2serlib import Handler  # type: ignore

# logging config:
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def threaded(func):
    """
    Decorate function for multithreading.

    Decorator that multithreads the target function
    with the given parameters. Returns the thread
    created for the function.
    """

    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


def str_to_dict(string):
    """Parse a string to a dictionary."""
    string = string.strip("{}")
    pairs = string.split(", ")
    return {
        key[1:-2]: str(value) for key, value in (pair.split(": ") for pair in pairs)
    }


class Westermo:
    """Class for interacting with the westermo switch."""

    def __init__(self, **kwargs) -> None:
        """Initialize the Class."""
        logger.debug("class init")
        self.DEVICE = kwargs
        self.telnet2serlib()
        sleep(0.2)

    def __enter__(self):  # -> None:
        """Run commands on class enter."""
        logger.debug("class entered")
        self.conn = Scrapli(**self.DEVICE)
        logger.debug("Scrapli initialized")
        self.conn.open()
        logger.debug("Scrapli connection opened")
        self.set_interactive()
        return self

    def __exit__(self, *args) -> None:
        """Run commands on class exit."""
        _ = args
        self.conn.close()

    @threaded
    def telnet2serlib(self):
        """Start the telnet to serial shim."""
        connections = Handler()
        while True:
            connections.run()

    def get_uptime(self) -> str:
        """Get the uptime of the switch."""
        uptime = self.conn.send_command("uptime")
        logger.debug("uptime: %s", uptime.result[1:9])
        return str(uptime.result[1:9])

    def get_sysinfo(self) -> dict:
        """Get system info and return it as a list|dict.

        Return:
            dict: System parameters dictionary
        """
        sysinfo = self.conn.send_command("show system-information")
        return_values: Any = list(
            sysinfo.ttp_parse_output(template="ttp_templates/system-information.txt")
        )[0]
        logger.debug("get_sysinfo function: %s", return_values)
        return return_values

    def get_mgmt_ip(self) -> list[dict]:
        """Get current management ip info."""
        ip_mgmt_info = self.conn.send_command("show ifaces")
        return_values: Any = list(
            ip_mgmt_info.ttp_parse_output(template="ttp_templates/show_ifaces.txt")
        )[0]
        logger.debug("get_mgmt_ip function: %s", return_values)
        return return_values

    def get_ports(self) -> list[dict]:
        """Get status of ports, and return it as a list|dict.

        Returns:
            list|dict: Status of all ports
        """
        status_ports = self.conn.send_command("show port")
        first_parse: Any = list(
            status_ports.ttp_parse_output(template="ttp_templates/ports.txt")
        )
        return_values = first_parse[0][2:]
        for keys in return_values:
            keys["port"] = int(keys["port"][4:])
            keys["vid"] = int(keys["vid"])
            if keys["link"] == "UP":
                keys["link"] = True
            else:
                keys["link"] = False
            if keys["alarm"] == "ALARM":
                keys["alarm"] = True
            elif keys["alarm"] == "None":
                keys["alarm"] = True
            else:
                keys["alarm"] = False
        logger.debug("get_ports function: %s", return_values)
        return return_values

    def get_frnt(self) -> list | dict:
        """Get status of ports, and returns it as a list|dict.

        Returns:
            list|dict: Status of all ports
        """
        status_ports = self.conn.send_command("show frnt")
        return_values: Any = list(
            status_ports.ttp_parse_output(template="ttp_templates/show_frnt.txt")
        )[0]
        logger.debug("get_ports function: %s", status_ports.result)
        return return_values

    def set_frtn(self, ports: tuple = (1, 2)) -> None:
        """Toggle the FRNT Ring."""
        if ports == (0):
            self.conn.send_config("no frnt 1")
            logger.debug("set_frnt function: disabling frnt")
        else:
            portstr = ",".join(str(x) for x in ports)
            self.conn.send_config(f"frnt 1 ring-ports {portstr}")
            logger.debug("set_frnt function: frnt set on port %s", portstr)

    def set_focal(self, member: bool = True) -> None:
        """Set member on the FRNT Ring."""
        if member:
            self.conn.send_config("frnt 1 no focal-point")
            logger.debug("set_focal function: member")
        else:
            self.conn.send_config("frnt 1 focal-point")
            logger.debug("set_focal function: master")

    def set_alarm(self, alarm: list[bool]) -> None:
        """Configure alarm when link down for interfaces in list.

        value == True is alarm on

        Args:
            alarm (list): interfaces with alarm on or off
        """
        port_list = ""
        for cnt, val in enumerate(alarm):
            if val is True:
                if port_list == "":
                    port_list = str(cnt + 1)
                else:
                    port_list += "," + str(cnt + 1)

        self.conn.send_config("alarm no action 1")  # unset alarmaction 1
        self.conn.send_config("alarm no trigger 1")  # unset alarmtrigger 1
        self.conn.send_config(
            f"alarm trigger 1 link-alarm condition low port {port_list}"
        )
        self.conn.send_config("alarm action 1 target led,log,digout")
        logger.debug("set_alarm function: set alarm on ifaces %s ON", port_list)

    def set_mgmt_ip(self, ip_add: str) -> bool:
        """Change the management ip-address of the switch to (ip).

        Args:
            ip_add (str): IP Address to set
        Returns:
            None
        """
        try:
            ip_address(ip_add)
        except ValueError:
            return False
        logger.debug("set_mgmt_ip function: setting vlan1 to static 192.168.2.200/24}")
        self.conn.send_config("iface vlan1 inet static address 192.168.2.200/24")
        self.conn.send_config("exit")
        logger.debug("set_mgmt_ip function: removing all secondary ip")
        self.conn.send_interactive(
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
        self.conn.send_config("exit")
        logger.debug("set_mgmt_ip function: setting vlan1 secondary to %s", ip_add)
        self.conn.send_config(f"iface vlan1 inet static address {ip_add}/24 secondary")
        return True

    def set_hostname(self, hostname: str) -> None:
        """Change the hostname of the switch.

        Args:
            hostname (str): Hostname to switch to
        """
        self.conn.send_config(f"system hostname {hostname}")
        logger.debug("conf_hostname function: set %s", hostname)

    def set_interactive(self, interactive: bool = True) -> None:
        """Set the interactive mode on the switch.

        This enables paging, but also lets you structure commands fully
        """
        if interactive:
            self.conn.send_command("interactive")
            logger.debug("Interactive mode set")
        else:
            self.conn.send_command("batch")
            logger.debug("Batch mode set")

    def set_location(self, location: str) -> None:
        """Change the location parameter of the switch.

        Args:
            location (str): location string to switch to
        """
        if location == "":
            self.conn.send_config("no system location")
            logger.debug("set_location function: removing location")
        else:
            location = re.sub("[^a-zA-Z0-9 \n\\.]", "", location)
            self.conn.send_config(f"system location '{location}'")
            logger.debug("set_location function: set to: %s", location)

    def factory_conf(self) -> None:
        """Reset device to factory defaults."""
        self.conn.send_interactive(
            [("factory-reset", "=> Are you sure (y/N)?", False), ("y", "", False)]
        )
        logger.debug("factory_conf function: Factory defaults set")

    def save_run2startup(self) -> bool:
        """Save the configuration from running to startup."""
        response = self.conn.send_command("copy run start")
        logger.debug("save_run2startup function: %s", response.result)
        if response.result != "":
            return False
        return True

    def save_config(self) -> str:
        """Get the startup config and returns it as a decoded string.

        Returns:
            config (str)
        """
        self.set_interactive(False)
        config = self.conn.send_command("show startup-config").result
        self.set_interactive(True)
        return config

    def compare_config(self) -> bool:
        """Compare the running and startup config and returns status.

        Returns:
            status (bool): True = Match
                           False = Mismatch
        """
        self.set_interactive(False)
        raw_startup = self.conn.send_command("show startup-config").result
        parsed_startup = "".join(raw_startup.splitlines(keepends=True)[:-4]).rstrip()
        raw_running = self.conn.send_command("show running-config").result
        self.set_interactive(True)
        if parsed_startup == raw_running:
            logger.debug("compare_config function: True")
            return True
        logger.debug("compare_config function: False")
        return False

    def get_alarm_log(self) -> list | dict:
        """Return the alarm log as a list | dict.

        Returns:
            eventlog (list | dict)
        """
        logger.debug("get_alarm_log function: ")
        returnobj = self.conn.send_command("show alarm")
        return_values: Any = list(
            returnobj.ttp_parse_output(template="ttp_templates/alarm_log.txt")
        )[0]
        logger.debug(return_values)
        return return_values

    def get_event_log(self) -> str:
        """Return the event list as a list | dict.

        Returns:
            log (str)
        """
        logger.debug("get_event_log function: ")
        self.set_interactive(False)
        return_values = self.conn.send_command("alarm log").result
        self.set_interactive(True)
        logger.debug(return_values)
        return return_values


if __name__ == "__main__":
    SWITCH = {
        "host": "127.0.0.1",
        "port": 2323,
        "auth_username": "admin",
        "auth_password": "westermo",
        "platform": "westermo_weos",
        "transport": "telnet",
        # "host": "192.168.2.200",
        # "auth_username": "admin",
        # "auth_password": "westermo",
        # "auth_strict_key": False,
        # "platform": "westermo_weos",
    }
    # alarms = [False,False,False,False,False,False,False,True,False,True]
    with Westermo(**SWITCH) as switch:
        switch.set_interactive()
        switch.get_sysinfo()
        switch.get_uptime()
        # switch.get_ports()
        # switch.save_config()
        # switch.compare_config()
        # switch.set_alarm(alarms)
        # switch.set_mgmt_ip('192.168.0.202')
        # switch.get_mgmt_ip()
        # switch.get_alarm_log()
        # switch.get_event_log()
        # switch.factory_conf()
        # switch.set_frtn()
        # switch.conn.send_config('exit')
        # switch.set_focal(member=True)
        # switch.get_frnt()
        # switch.save_run2startup()
        input()
