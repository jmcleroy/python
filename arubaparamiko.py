#!/usr/bin/python
#
import paramiko
import time
import re

host = '172.16.1.82'
user = 'manager'
passwd = 'manager'


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


stdin.send('\n') # Get past "Press any key"
stdout()
stdin.send('\nshow version\n')
stdout()
stdin.send('\nshow interfaces\n')
stdout()