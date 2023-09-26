#!/usr/bin/python3
""" Westermo_lib.

This module uses a ssh connection to communicate with Westermo, 
currently only testet on the lynx range for common configuring.

Todo:
    # set time : configure -> clock set hh:mm:ss month day year

class fileHandler:
    def __init__(self, dbf):
        self.logger = logging.getLogger('fileHandler')
        self.thefilename = dbf
    def __enter__(self):
        self.thefile = open(self.thefilename, 'rb')
        return self
    def __exit__(self, *args):
        self.thefile.close()


"""
from ipaddress import ip_address
from scrapli import Scrapli # type: ignore

class Westermo:
    """
    Class for interacting with the westermo switch
    """
    def __init__(self, verbose:bool=False, **kwargs) -> None:
        self.verbose = verbose
        self.DEVICE = kwargs

    def __enter__(self): # -> None:
        # self.conn = GenericDriver(**self.DEVICE)
        self.conn = Scrapli(**self.DEVICE)
        self.conn.open()
        return self

    def __exit__(self, *args) -> None:
        _ = args
        self.conn.close()

    def vprint(self, text) -> None:
        """
        Prints only when verbose is true
        """
        if self.verbose is True:
            print(f'Westermo_weos: {text}')


    def get_uptime(self) -> str:
        uptime = self.conn.send_command('uptime')
        self.vprint(uptime.result[1:9])
        return str(uptime.result[1:9])

    def get_sysinfo(self) -> dict:
        """ Gets system info and returns it as a list|dict

        Returns:
            dict: System parameters dictionary
        """
        sysinfo = self.conn.send_command('show system-information')
        return_values = sysinfo.ttp_parse_output(
            template='ttp_templates/system-information.txt')
        self.vprint(f'get_sysinfo function: {return_values[0]}')
        return return_values[0]


    def get_mgmt_ip(self) -> list[dict]:
        """ Gets current management ip info
        """
        ip_mgmt_info = self.conn.send_command('show ifaces')
        return_values = ip_mgmt_info.ttp_parse_output(
            template='ttp_templates/show_ifaces.txt')
        self.vprint(f'get_mgmt_ip function: {list(return_values)[0]}')
        return return_values[0]


    def get_ports(self) -> list[dict]:
        """ Gets status of ports, and returns it as a list|dict.

        Returns:
            list|dict: Status of all ports
        """
        status_ports = self.conn.send_command('show port')
        first_parse = status_ports.ttp_parse_output(
            template='ttp_templates/ports.txt')
        return_values = first_parse[0][2:]
        for keys in return_values:
            keys['port'] = int(keys['port'][4:])
            keys['vid'] = int(keys['vid'])
            if keys['link'] == 'UP':
                keys['link'] = True
            else:
                keys['link'] = False
            if keys['alarm'] == 'ALARM':
                keys['alarm'] = True
            else:
                keys['alarm'] = False
        self.vprint(f'get_ports function: {return_values}')
        return return_values

    def get_frnt(self) -> list|dict:
        """ Gets status of ports, and returns it as a list|dict.

        Returns:
            list|dict: Status of all ports
        """
        status_ports = self.conn.send_command('show frnt')
        return_values = status_ports.ttp_parse_output(
            template='ttp_templates/show_frnt.txt')
        self.vprint(f'get_ports function: {status_ports.result}')
        return return_values

    def set_frtn(self, ports=[1,2]) -> None:
        """ Sets up the FRNT Ring
        """
        portstr = ','.join(str(x) for x in ports)
        self.conn.send_config(f'frnt 1 ring-ports {portstr}' )
        self.vprint(f'set_frnt function: frnt set on port {portstr}')

    def set_focal(self) -> None:
        """ Set member on the FRNT Ring
        """
        self.conn.send_config('frnt 1 no focal-point' )
        self.vprint('set_focal function: member')


    def set_alarm(self, alarm:list[bool]) -> None:
        """ Configures alarm when link down for interfaces in list.

        value == True is alarm on

        Args:
            alarm (list): interfaces with alarm on or off
        """
        port_list = ''
        for cnt, val in enumerate(alarm):
            if cnt <= 0:
                if val is True:
                    port_list = str(cnt + 1)
            else:
                if val is True:
                    port_list += ',' + str(cnt + 1)

        self.conn.send_config('alarm no action 1') # unset alarmaction 1
        self.conn.send_config('alarm no trigger 1') # unset alarmtrigger 1
        self.conn.send_config(
            f'alarm trigger 1 link-alarm condition low port {port_list}')
        self.conn.send_config('alarm action 1 target led,log,digout')
        self.vprint(alarm)
        self.vprint(f'set_alarm function: set alarm on ifaces {port_list} ON')


    def set_mgmt_ip(self, ip_add:str) -> bool:
        """ Changes the management ip-address of the switch to (ip)

        Args:
            ip_add (str): IP Address to set
        Returns:
            None
        """
        try:
            ip_address(ip_add)
        except ValueError:
            return False
        # self.conn.send_interactive(
        #                         [('iface vlan1 inet static no address secondary'
        #                           ,'=> Are you sure (y/N)?', False),
        #                          ('y', '', False)])
        # self.conn.send_config(f'iface vlan1 inet static address {ip_add}/24 secondary')
        self.vprint(f'set_mgmt_ip function: setting vlan1 to {ip_add}')
        return True

    def set_hostname(self, hostname:str) -> None:
        """ Changes the hostname of the switch

        Args:
            hostname (str): Hostname to switch to
        """
        self.conn.send_config(f'system hostname {hostname}')
        self.vprint(f'conf_hostname function: set {hostname}')


    def set_location(self, location:str) -> None:
        """ Changes the location parameter of the switch

        Args:
            location (str): location string to switch to
        """
        if location == '':
            self.conn.send_config('no system location')
            self.vprint('set_location function: removing location')
        else:
            self.conn.send_config(f'system location {location}')
            self.vprint(f'set_location function: set to: {location}')


    def factory_conf(self) -> None:
        """ Reset device to factory defaults
        """
        self.conn.send_interactive(
                                [('factory-reset' ,'=> Are you sure (y/N)?', False),
                                 ('y', '', False)])
        self.vprint('factory_conf function: Factory defaults set')


    def save_run2startup(self) -> bool:
        """ Saves the configuration from running to startup
        """
        response = self.conn.send_command('copy run start')
        self.vprint(f'save_run2startup function: {response.result}')
        if response.result != '':
            return False
        return True



    def save_config(self) -> str:
        """ Gets the startup config and returns it as a decoded string

        Returns:
            config (str)
        """
        config = self.conn.send_command('show startup-config').result
        return config


    def compare_config(self) -> bool:
        """ Compares the running and startup config and returns status

        Returns:
            status (bool): True = Match
                           False = Mismatch
        """
        raw_startup = self.conn.send_command('show startup-config').result
        parsed_startup = ''.join(raw_startup.splitlines(keepends=True)[:-4]).rstrip()
        raw_running = self.conn.send_command('show running-config').result
        if parsed_startup == raw_running:
            self.vprint('compare_config function: True')
            return True
        self.vprint('compare_config function: False')
        return False

    def get_alarm_log(self) -> list | dict:
        """ Returns the alarm log as a list | dict

        Returns:
            eventlog (list | dict)
        """
        self.vprint('get_alarm_log function: ')
        returnobj = self.conn.send_command('show alarm')
        return_values = returnobj.ttp_parse_output(
            template='ttp_templates/alarm_log.txt')[0]
        self.vprint(return_values)
        return return_values

    def get_event_log(self) -> str:
        """ Returns the event list as a list | dict

        Returns:
            log (str)
        """
        self.vprint('get_event_log function: ')
        return_values = self.conn.send_command('alarm log').result
        self.vprint(return_values)
        return return_values


if __name__ == "__main__":
    SWITCH = {
        'host': '192.168.2.200',
        'auth_username': 'admin',
        'auth_password': 'westermo',
        'auth_strict_key': False,
        'platform': 'westermo_weos'
    }
    alarms = [1,2,10]

    with Westermo(verbose=True, **SWITCH) as switch:
        # switch.get_sysinfo()
        # switch.get_uptime()
        switch.get_ports()
        # switch.save_config()
        # switch.compare_config()
        # switch.set_alarm(alarms)
        # switch.set_mgmt_ip('192.168.2.200')
        # switch.get_mgmt_ip()
        # switch.get_alarm_log()
        # switch.get_event_log()
        # switch.factory_conf()
        # switch.set_frtn()
        # switch.set_focal()
        # switch.save_run2startup()
        input()
