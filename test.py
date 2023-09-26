#!/usr/bin/env python
# -*- coding=utf-8 -*-

from ttp import ttp

data_sysinfo = """
Ethernet ----------------------------------------------------------------------
Port    Link Type          Speed      State      Alarm   VID  MAC Address      
===============================================================================
Eth 1   DOWN 1000-SFP      ---------- ---------- ALARM     1  00:11:b4:5e:e0:81
Eth 2   DOWN 1000-SFP      ---------- ---------- ALARM     1  00:11:b4:5e:e0:82
Eth 3   DOWN 10/100TX      ---------- ----------   N/A     1  00:11:b4:5e:e0:83
Eth 4   DOWN 10/100TX      ---------- ----------   N/A     1  00:11:b4:5e:e0:84
Eth 5   DOWN 10/100TX      ---------- ----------   N/A     1  00:11:b4:5e:e0:85
Eth 6     UP 10/100TX      100M-Full  Forwarding   N/A     1  00:11:b4:5e:e0:86
Eth 7   DOWN 10/100TX      ---------- ----------   N/A     1  00:11:b4:5e:e0:87
Eth 8   DOWN 10/100TX      ---------- ----------   N/A     1  00:11:b4:5e:e0:88
Eth 9   DOWN 10/100TX      ---------- ----------   N/A     1  00:11:b4:5e:e0:89
Eth 10  DOWN 10/100TX      ---------- ---------- ALARM     1  00:11:b4:5e:e0:8a
"""

data_alarmlog = """
No Trigger          Ena Act Reason                        
===============================================================================
 1 link-alarm       YES YES Port 1,4-5 DOWN                                   
 2 link-alarm       YES YES Port 6 DOWN
"""

data_ifaces = """
Press Ctrl-C or Q(uit) to quit viewer, Space for next page, <CR> for next line.

Interface Name    Oper  Address/Length      MTU    MAC/PtP Address
----------------  ----  ------------------  -----  ---------------------------
lo                UP    127.0.0.1/8         16436  N/A              
vlan1             UP    192.168.2.200/24    1500   00:11:b4:5e:e0:81
                        169.254.234.22/16
------------------------------------------------------------------------------
"""

data_frnt = """
                       Top
 Rid  Ver   Status     Cnt   Mode       Port 1               Port 2
===============================================================================
   1   0    Broken       0   Member     Eth 1 Down           Eth 2 Down
-------------------------------------------------------------------------------
"""



alarmlog_template = """
 <group name='alarm_log'>
 {{ id | to_int() }} {{ trigger }}          {{ enabled }} {{ active }} {{ ignore }} {{ port | unrange('-', ',') | split(',') }} {{ state }}
</group>
"""

"""
{{ ignore }} {{ port | to_int() }}   {{ link | to_str() }} {{ type }}          {{ speed }}      {{ state }}      {{ alarm }}   {{ vlan_id | to_int() }}  {{ mac_address | to_str() }} 
 r_id ver status     count   mode       port_1               port_2 {{ _headers_ | columns(7)}}
    {{ r_id }} {{ version }} {{ status }}  {{ top_cnt }} {{ mode }} {{ port 1}} {{ port 2}}
"""

ifaces_template = """
<group name='ifaces'>
{{ iface_name }} {{ operation }} {{ primary_ip | is_ip }} {{ mtu | to_int }} {{ mac }}
                        {{ secondary_ip | is_ip }}
</group>
"""

frnt_template = """
<group name = "frnt_config">
{{ignore}}
 r_id ver status     count   mode       port_1               port_2 {{ _headers_ | columns(7)}}
</group>
"""

sysinfo_template = """
<group>
=============================================================================== {{ _start_ }}
port    link type          speed      state      alarm   vid  mac_address      {{ _headers_}}
    </group>
"""

# parser = ttp(data=data_sysinfo, template=sysinfo_template)
# parser = ttp(data=data_alarmlog, template=alarmlog_template)
# # parser = ttp(data=data_sysinfo, template=sysinfo_template)
# parser.parse()
# results = parser.result(format='json')[0]
# print(results)
alarm = [True, True, False, True, False, False, False, False, False, True]
port_list = ''
for cnt, val in enumerate(alarm):
    if cnt <= 0:
        if val is True:
            port_list = str(cnt + 1)
    else:
        if val is True:
            port_list += ',' + str(cnt + 1)

print(port_list)

input()

