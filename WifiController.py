# -*- coding: UTF-8 -*-
#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk

from subprocess import check_output
import os
import time
import threading


class WifiWindowController(Gtk.Window):

    wifiModel = Gtk.ListStore(str, bool, str)
    currentIter = None
    currssid = ""


    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("WifiWindow.glade")
        self.window = self.builder.get_object("windowWifi")
        self.window.show_all()

        renderer = Gtk.CellRendererText()

        self.notebook = self.builder.get_object("notebook")
        self.notebook.set_show_tabs(False)

        self.fieldPass = self.builder.get_object("fieldPass")

        self.tableWifi = self.builder.get_object("tableWifi")
        self.tableWifi.set_model(self.wifiModel)
        column = Gtk.TreeViewColumn("  ", renderer, text=2)
        self.tableWifi.append_column(column)
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        self.tableWifi.append_column(column)
        #self.selectionWifi = self.builder.get_object("treeview-selection1")
        
        #self.window.fullscreen()
        self.window.present()  #key win
        self.builder.connect_signals(self)
    


    def closeWinPressed(self, button):
        self.window.destroy()

    def refreshPressed(self,button):
        self.builder.get_object("spinnerRefresh").start()
        startSpinnerThread = threading.Thread(target=self.refreshTable)
        startSpinnerThread.start()
   
    def refreshTable(self):
        res = os.popen("sudo iwgetid").read()
        self.currssid = ""
        if "ESSID:" in res :
            spli = res.split('ESSID:"')
            if len(spli) > 1:
                self.currssid = spli[1]
                self.currssid = self.currssid.replace('"', "")
                self.currssid = self.currssid.replace("\n", "")
            
        self.wifiModel.clear()
        os.popen("sudo ifconfig wlan0 down")
        stat = os.popen("sudo ifconfig wlan0 up").read()
        if "No such device" in stat:
            print("nessun dispositivo di rete trovato")
            return
        stream = os.popen("sudo iwlist wlan0 scan")
        rete = ""
        enc = ""
        for line in stream:
            if "Cell" in line:
                rete = None
                enc = None
            if "Encryption key" in line:
                enc = line.split(":")[1]
                enc = enc.replace("\n", "")

            if "ESSID" in line:
                rete = line.lstrip().split("ESSID:")[1]
                rete = rete.replace('"', "")
                rete = rete.replace("\n", "")
                if rete == "" or rete == "\n" or rete.isspace() or rete == " " or len(rete) == 0:
                    rete = None
            
            if rete != None and enc != None:
                if len(rete) > 0:
                    if self.currssid == rete:
                        spunta = "✓"
                    else:
                        spunta = ""
                    
                    if enc == "on\n" or enc == "on":
                        needP = True
                    else:
                        needP = False

                    self.wifiModel.append([rete, needP, spunta])
                    rete = None
                    enc = None
        self.builder.get_object("spinnerRefresh").stop()
            
    def wifiSelected(self, selection):

        model,iterator = selection.get_selected()
        if iterator == None:
            return
        ssid = model[iterator][0]
        if ssid == "":
            return
        if self.currssid == ssid:
            print("gia connesso")
            return
                
        self.currentIter = iterator
        self.builder.get_object("labelWifiTitle").set_label(ssid)
        self.builder.get_object("labelWifiMessage").set_label("")
        self.builder.get_object("spinnerWifi").stop()
        if model[iterator][1] == True: #ce la pass
            self.builder.get_object("labelPass").set_visible(True)
            self.builder.get_object("fieldPass").set_visible(True)
        else:
            self.builder.get_object("labelPass").set_visible(False)
            self.builder.get_object("fieldPass").set_visible(False)   
        self.notebook.set_current_page(1)
        return

        """
        print("provo a connettermi a " + ssid)
        path = "/etc/wpa_supplicant/wpa_supplicant.conf"
        with open(path, "a+") as wpaFile: #  a = append
            if ssid in wpaFile:
                print("esiste gia")  #qui devo chiedere la pass
                os.popen("sudo wpa_cli reconfigure")
                return
            if model[iterator][1] == True: #ce la pass
                newNet = '\nnetwork={\nssid="iPhone di mattia de vidi" \n psk="marte1985"\n priority=100\n}'
            else:
                newNet = '\nnetwork={\nssid="iPhone di mattia de vidi" \n key_mgmt=NONE\n priority=100\n}'
            wpaFile.write(newNet)
            os.popen("sudo wpa_cli reconfigure")"""
            
    def connectPressed(self, button):
        if self.currentIter == None:
            return
        print("prosegue")
        ssid = self.wifiModel[self.currentIter][0]
        if self.wifiModel[self.currentIter][1] == True:  #ce pass
            if self.fieldPass.get_text() == "":
                self.builder.get_object("labelWifiMessage").set_label("Enter Password !")
                return
        password = self.fieldPass.get_text()
        print("provo a connettermi a " + ssid)
        path = "/etc/wpa_supplicant/wpa_supplicant.conf"
        with open(path, "r+") as wpaFile:  
            fileStr = wpaFile.read()
            maxPriority = 1
            networks = fileStr.split("network")
            for net in networks:
                index = net.find("priority")
                if index != -1:
                    index = index + 8
                    for ind in range(index, len(net) - 1):
                        if net[ind] == "=":
                            startInd = ind + 1
                        if not net[ind].isspace():
                            if not net[ind].isdigit():
                                endInd = ind - 1
                                try:
                                    prio = int(net[startInd : endInd])
                                    if maxPriority <= prio:
                                        maxPriority = prio + 1
                                except ValueError:
                                    print("errore lettura priority")
                                    
            ssidInd = fileStr.find(ssid)
            startInd = None
            endInd = None
            if ssidInd is not -1:     #se esiste gia una rete con ssid uguale, lo elimino
                for i in range(ssidInd, 0):
                    if fileStr[i : i + 7] == "network":
                        startInd = i
                        break
                for i in range(ssidInd, len(fileStr)):
                    if fileStr[i] == "}":
                        endInd = i + 1
                        break   
                if startInd != None and endInd != None:
                    fileStr = fileStr.replace(fileStr[startInd : endInd], "")

            #aggiungo la nuova rete alla fine del file
                        
            if self.wifiModel[self.currentIter][1] == True: #password necessaria
                newNet = '\nnetwork={\n\tssid="' + ssid + '"   \n\tpsk="' + password + '"\n\tpriority=' + str(maxPriority) + '\n}'
            else:
                newNet = '\nnetwork={\n\tssid="' + ssid + '" \n\tkey_mgmt=NONE\n\tpriority=' + str(maxPriority) + '\n}'
            fileStr = fileStr + newNet
            wpaFile.seek(0)
            wpaFile.truncate()
            wpaFile.write(fileStr)
                
        os.popen("sudo wpa_cli reconfigure")   #restart wpa
        self.builder.get_object("labelWifiMessage").set_label("Connecting ...")
        self.builder.get_object("spinnerWifi").start()
            
    def backPressed(self, button):
        self.currentIter = None
        self.builder.get_object("spinnerWifi").stop()
        self.notebook.set_current_page(0)
    

    
