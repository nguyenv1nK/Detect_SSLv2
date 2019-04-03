import json
import os
import socket
import struct
import subprocess


def get_ip_address_linux():
    list_iface = os.listdir('/sys/class/net')
    list_ips = []
    import fcntl
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for iface in list_iface:
        try:
            list_ips.append(socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', iface[:15])
            )[20:24]))
        except:
            pass
    return list_ips


def get_my_ip():
    try:
        return get_ip_address_linux()
    except:
        pass
    addr_list = socket.getaddrinfo(socket.gethostname(), None)
    list_ips = []
    for item in addr_list:
        try:
            socket.inet_aton(item[4][0])
            list_ips.append(item[4][0])
        except socket.error:
            pass
    return list_ips


def get_ip_win():
    list_iface = []
    command = "netsh interface ip show config"
    netshcmd = subprocess.Popen(command, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=None)
    output = str(netshcmd.communicate()).split('IP Address:')
    for split in output:
        if '"' in split:
            iface = split.split('"')[0]
            list_iface.append(split.split('"')[0])


