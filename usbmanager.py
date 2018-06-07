# -*- coding: UTF-8 -*-
#!/usr/bin/python3


import usb.core
import usb.util
import sys
import subprocess
import evdev, asyncio



class DeviceMassStorage:
    label = ""
    url = ""
    mountedUrl = ""


def getUsbDevices():
    res = subprocess.check_output(["ls","-l","/dev/disk/by-uuid/"]).decode("unicode_escape")
    mounted = subprocess.check_output(["ls","/media/pi/"]).decode("unicode_escape").split("\n")
    
    
    rows = res.split("\n")
    del rows[0]
    devices = []
    for row in rows:
        words = row.split()
        if len(words) != 0:
            if words[8] != "boot":
                arrowIndex = words.index("->")
                labelList = words[8:arrowIndex]
                new = DeviceMassStorage()
                new.label = " ".join(labelList)
                urlList = words[len(words) - 1].split("/")
                url = urlList[len(urlList) - 1]
                new.url = "/dev/" + url
                new.mountedUrl = "/media/pi/" + new.label + "/"
                if new.label in mounted:
                    devices.append(new)
        
    return devices
"""
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
for device in devices:
    print(device.fn, device.name)

keyboard = evdev.InputDevice('/dev/input/event2')
rfid = evdev.InputDevice('/dev/input/event1')
"""


"""
for event in keyboard.read_loop():
    if event.type == evdev.ecodes.EV_KEY:
        data = evdev.categorize(event)
        if data.keystate == 1: #down event only
            print(data.keycode)"""
            

        
