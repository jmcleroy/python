#!/usr/bin/python
#
from paramiko import ConnectHandler

A3810_1 = {
    'device_type':'hp_procurve',
    'ip':'172.16.1.82',
    'username':'manager',
    'password':'manager',
}

net_connect = ConnectHandler(**A3810_1)

output = net_connect.send_command("show version")

print output