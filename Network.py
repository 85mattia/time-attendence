#from wifi import Cell,Scheme

import sys
#from pyroute2 import IW
#from pyroute2 import IPRoute
#from pyroute2.netlink import NetlinkError

import socket
import fcntl
import struct
import subprocess
import time
import argparse
from subprocess import check_output
from uuid import getnode
import os

parser = argparse.ArgumentParser(description='Display WLAN signal strength.')
parser.add_argument(dest='interface', nargs='?', default='wlan0',
                    help='wlan interface (default: wlan0)')
args = parser.parse_args()



def isWifiNetwork():
    return True
    
    """

    ip = IPRoute()
    iw = IW()
    index = ip.link_lookup(ifname="wlan0")[0]
    try:
        iw.get_interface_by_ifindex(index)
        iw.close()
        ip.close()
        return True
    except NetlinkError as e:
        if e.code == 19:  # 19 'No such device'
            iw.close()
            ip.close()
            return False
        
    finally:
        iw.close()
        ip.close()
    """
    
def getWifiPower():
    cmd = subprocess.Popen('iwconfig %s' % args.interface, shell=True,
                           stdout=subprocess.PIPE)
    for line in cmd.stdout:
        if "Signal level" in str(line,"utf-8"):
            db = int(str(line,"utf-8").split()[3].replace("level=",""))
            
            return getLevel(db)
def getLevel(db):
    if db >= -30:
        return "OOOO"
    elif db > -67:
        return "OOO -"
    elif db > -70:
        return "OO - -"
    elif db > -90:
        return "O - - -"
    else:
        return "- - - -"

"""    
def getCurrentSsid():
    
    scanoutput = check_output(["iwgetid"])
    ssid = ""
    for line in scanoutput.split():
        line = line.decode("utf-8")
        if line[:5]  == "ESSID":
            ssid = line.split('"')[1]
    print("ora sono connesso a " +ssid)
    #print("trovato " +check_output(["iwlist","scan"]).splitlines())
    return ssid
def connect(network,tpass = None):
    print("provo a conneteremi a " + network)
    if tpass == None:
        res = os.system("sudo iwconfig " + "wlan0" + " essid " + network)
    else:
        res = os.system("sudo iwconfig " + "wlan0" + " essid " + network + " key s:" + tpass)
    print("res= "+str(res))
    print("finito")    """    
        
def getIpAddress():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return None
def getMacAddress():
    add = getnode()
    h = iter(hex(add)[2:].zfill(12))
    return ":".join(i + next(h) for i in h)

