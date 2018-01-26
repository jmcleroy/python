#!/usr/bin/env python

DOCUMENTATION = '''
---
module: arubaparamikomodule
short_description: Writes config data to devices that don't have an API
description:
    - This module write config data to devices that don't have an API.
      The use case would be writing configuration based on output gleaned
      from ntc_show_command output.
author: Eric McLeroy (@jmcleroy)
requirements:
    - paramiko
options:
    connection:
        description:
            - connect to device using netmiko or read from offline file
              for testing
        required: false
        default: ssh
        choices: ['ssh', 'telnet']
    platform:
        description:
            - Platform FROM the index file
        required: false
    commands:
        description:
            - Command to execute on target device
        required: false
        default: null
    commands_file:
        description:
            - Command to execute on target device
        required: false
    host:
        description:
            - IP Address or hostname (resolvable by Ansible control host)
        required: false
    provider:
        description:
          - Dictionary which acts as a collection of arguments used to define the characteristics
            of how to connect to the device.
            Note - host, username, password and platform must be defined in either provider
            or local param
            Note - local param takes precedence, e.g. hostname is preferred to provider['host']
        required: false
    port:
        description:
            - SSH port to use to connect to the target device
        required: false
        default: 22 for SSH. 23 for Telnet
    username:
        description:
            - Username used to login to the target device
        required: false
        default: null
    password:
        description:
            - Password used to login to the target device
        required: false
        default: null
    secret:
        description:
            - Password used to enter a privileged mode on the target device
        required: false
        default: null
    use_keys:
        description:
            - Boolean true/false if ssh key login should be attempted
        required: false
        default: false
    key_file:
        description:
            - Path to private ssh key used for login
        required: false
        default: null
'''

EXAMPLES = '''
vars:
  nxos_provider:
    host: "{{ inventory_hostname }}"
    username: "ntc-ansible"
    password: "ntc-ansible"
    platform: "cisco_nxos"
    connection: ssh
# write vlan data
- ntc_config_command:
    connection: ssh
    platform: cisco_nxos
    commands:
      - vlan 10
      - name vlan_10
      - end
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    secret: "{{ secret }}"
# write config from file
- ntc_config_command:
    connection: ssh
    platform: cisco_nxos
    commands_file: "dynamically_created_config.txt"
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    secret: "{{ secret }}"
- ntc_config_command:
    commands:
      - vlan 10
      - name vlan_10
      - end
    provider: "{{ nxos_provider }}"
'''

#
import paramiko
import time
import re

def stdout():
    tCheck = 0
    while not stdin.recv_ready():
        time.sleep(1)
        tCheck+=1
        if tCheck >=10:
            print "time out"
    formatstdout(stdin.recv(1024))

def formatstdout(message):
   message = arubaos_re1.sub("", message)
   message = arubaos_re2.sub("", message)
   message = arubaos_re3.sub("", message)
   print message

arubaos_re1 = re.compile(r'(\[\d+[HKJ])|(\[\?\d+[hl])|(\[\d+)|(\;\d+\w?)')
arubaos_re2 = re.compile(r'([E]\b)')
arubaos_re3 = re.compile(ur'[\u001B]+') #remove escapes

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=passwd,look_for_keys=False)
stdin = ssh.invoke_shell()
stdout()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            connection=dict(choices=['ssh', 'telnet'],
                            default='ssh'),
            platform=dict(required=False),
            commands=dict(required=False, type='list'),
            commands_file=dict(required=False),
            host=dict(required=False),
            port=dict(required=False),
            provider=dict(type='dict', required=False),
            username=dict(required=False, type='str'),
            password=dict(required=False, type='str', no_log=True),
            secret=dict(required=False, type='str', no_log=True),
            use_keys=dict(required=False, default=False, type='bool'),
            key_file=dict(required=False, default=None, type='str'),
        ),
        supports_check_mode=False
    )

    provider = module.params['provider'] or {}

    no_log = ['password', 'secret']
    for param in no_log:
        if provider.get(param):
            module.no_log_values.update(return_values(provider[param]))

    # allow local params to override provider
    for param, pvalue in provider.items():
        if module.params.get(param) != False:
            module.params[param] = module.params.get(param) or pvalue

    host = module.params['host']
    connection = module.params['connection']
    platform = module.params['platform']
    device_type = platform.split('-')[0]
    commands = module.params['commands']
    commands_file = module.params['commands_file']
    username = module.params['username']
    password = module.params['password']
    secret = module.params['secret']
    use_keys = module.params['use_keys']
    key_file = module.params['key_file']

    argument_check = {'host': host, 'username': username, 'platform': platform, 'password': password}
    for key, val in argument_check.items():
        if val is None:
            module.fail_json(msg=str(key) + " is required")

    if module.params['host']:
        host = socket.gethostbyname(module.params['host'])

    if connection == 'telnet' and platform != 'cisco_ios':
        module.fail_json(msg='only cisco_ios supports '
                             'telnet connection')

    if platform == 'cisco_ios' and connection == 'telnet':
        device_type = 'cisco_ios_telnet'

    if module.params['port']:
        port = int(module.params['port'])
    else:
        if connection == 'telnet':
            port = 23
        else:
            port = 22

    if connection in ['ssh', 'telnet']:
        device = ConnectHandler(device_type=device_type,
                                ip=socket.gethostbyname(host),
                                port=port,
                                username=username,
                                password=password,
                                secret=secret,
                                use_keys=use_keys,
                                key_file=key_file
                                )

        if secret:
            device.enable()

        if commands:
            output = device.send_config_set(commands)
        else:
            try:
                if commands_file:
                    if os.path.isfile(commands_file):
                        with open(commands_file, 'r') as f:
                            output = device.send_config_set(f.readlines())
            except IOError:
                module.fail_json(msg="Unable to locate: {}".format(commands_file))

    if (error_params(platform, output)):
        module.fail_json(msg="Error executing command:\
                         {}".format(output))

    results = {}
    results['response'] = output

    module.exit_json(changed=True, **results)


from ansible.module_utils.basic import *

if __name__ == "__main__":
    main()