#!/usr/bin/env python3
# -*- coding=utf-8 -*-

from westermo_ser_lib import Westermo


if __name__ == "__main__":

    SWITCH = {
        'host': '192.168.2.200',
        'auth_username': 'admin',
        'auth_password': 'westermo',
        'auth_strict_key': False,
        'platform': 'westermo_weos'
    }

    with Westermo(verbose=True, **SWITCH) as switch:
        sysinfo = switch.get_sysinfo()
        ports = switch.get_ports()
        mgmt_ip = switch.get_mgmt_ip()
        frnt = switch.get_frnt()
        # switch.get_sysinfo()
        # switch.get_ports()
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
        input()
