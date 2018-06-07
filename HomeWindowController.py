# -*- coding: UTF-8 -*-
#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, GLib
from datetime import datetime, timezone, timedelta
from tzlocal import get_localzone
from DataManager import DataManager
import pytz
import Network
import configparser
import dateutil.parser
from operator import itemgetter, attrgetter
import subprocess
from time import sleep
import csv
import os
#from usbmanager import *
from WifiController import WifiWindowController
from GpioPort import *
import threading 
import socket

userModel = Gtk.ListStore(int,str,str,str)
logModel = Gtk.ListStore(str,str,str,str)
rateModel = Gtk.ListStore(str,str)
#usbModel = Gtk.ListStore(str,str,str)

try:
    config = open('defaults.ini', 'r+')
except Exception: #file non esiste
    with open('defaults.ini', 'a+') as f:
        f.seek(0)
        f.write("[STATUS]\n[SETTINGS]")
        f.truncate()
        os.chmod('defaults.ini', 0o666)
        
config = configparser.ConfigParser()
config.read("defaults.ini")


class HomeWindowController(Gtk.Window):

    userIdToEdit = None
    readCardString = ""
    keyTimeOut = False
    reVerifyMin = 0
    
    redColor = Gdk.color_parse("red")
    greenColor = Gdk.color_parse("green")
    orangeColor = Gdk.Color(red=65535, green=30000, blue=0)
    blueColor = Gdk.Color(red=0, green=0, blue=65500)
    blackColor = Gdk.Color(red=0, green=0, blue=0)
    funcToExecuteOnConfirm = None
    managerRun = False
    sound = Sound()
    isFullScreen=True
    
    def __init__(self):
        
        self.checkSettings()
    
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file("MainWindow.glade")  #problema
       
        self.window = self.builder.get_object("windowMain")
    
        
        
        self.cssProvider = Gtk.CssProvider()
        self.cssProvider.load_from_path('customcss.css')
        self.screen = Gdk.Screen.get_default()
        self.styleContext = Gtk.StyleContext()
        self.styleContext.add_provider_for_screen(self.screen, self.cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        
        #self.builder.get_object("buttonExitMenu").connect("clicked", self.exitMenuPressed)
        
        self.notebook = self.builder.get_object("notebook")
        self.spinButtonId = self.builder.get_object("spinbuttonId")
        adj = Gtk.Adjustment(0,0,9999,1,1,1)
        self.spinButtonId.configure(adj,1,0)
        
        self.spinButtonMaxLogs = self.builder.get_object("spinButtonMaxLogs")
        adj = Gtk.Adjustment(1000, 1000, 19000, 1000, 1, 1)
        self.spinButtonMaxLogs.configure(adj, 1, 0)

        self.spinbuttonVerify = self.builder.get_object("spinbuttonVerify")
        adj = Gtk.Adjustment(1,1,99,1,1,1)
        self.spinbuttonVerify.configure(adj,1,0)
        
        self.tableViewUser = self.builder.get_object("usersList")
        self.tableViewUser.grab_focus = self.treeViewGrabFocus
        self.selectionUser = self.builder.get_object("tableUserSelection")
        self.tableViewUser.set_model(userModel)
        self.tableViewUser.set_can_focus(False)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("ID",renderer,text=0)
        self.tableViewUser.append_column(column)
        column = Gtk.TreeViewColumn("Name",renderer,text=1)
        self.tableViewUser.append_column(column)
        column = Gtk.TreeViewColumn("Group",renderer,text=2)
        self.tableViewUser.append_column(column)

       
        self.tableViewLog = self.builder.get_object("tableLogs")
        self.tableViewLog.grab_focus = self.treeViewGrabFocus
        self.tableViewLog.set_can_focus(False)
        self.tableViewLog.set_model(logModel)
        column = Gtk.TreeViewColumn("UserID",renderer,text=0)
        self.tableViewLog.append_column(column)
        column = Gtk.TreeViewColumn("DateTime",renderer,text=1)
        self.tableViewLog.append_column(column)
        #column.set_sort_column_id(1)
        column = Gtk.TreeViewColumn("Status",renderer,text=2)
        self.tableViewLog.append_column(column)
        #column.set_sort_column_id(1)
        
        self.notebook.set_show_tabs(False)
        self.labelOrario = self.builder.get_object("labelOrario")
        self.labelOrario.set_label(datetime.now(pytz.timezone('Europe/Berlin')).strftime('%H:%M:%S'))
        self.labelInOut = self.builder.get_object("labelInOut")
        self.window.connect("destroy", Gtk.main_quit)
        self.builder.connect_signals(self)
        self.window.show_all()
        self.labelInOut.set_label(str(config["STATUS"]["lastStatus"]))

        self.builder.get_object("labelMessage").set_label("--")
        self.builder.get_object("labelUserMessage").set_label("")
        
        self.builder.get_object("buttonDeleteUser").modify_fg(Gtk.StateType.NORMAL,self.redColor)
        self.builder.get_object("buttonSaveUser").modify_fg(Gtk.StateType.NORMAL,self.greenColor)
        self.builder.get_object("buttonDeletaAllLogs").modify_fg(Gtk.StateType.NORMAL,self.redColor)
        self.builder.get_object("buttonMenu").modify_fg(Gtk.StateType.NORMAL, self.blueColor)
        self.builder.get_object("buttonIn").modify_fg(Gtk.StateType.NORMAL, self.blackColor)
        self.builder.get_object("buttonOut").modify_fg(Gtk.StateType.NORMAL, self.blackColor)
        
        self.reVerifyMin = int(config["STATUS"]["verifytime"])
        self.maxLogs = int(str(config["SETTINGS"]["maxLogs"]))
        
        self.window.fullscreen()
        GObject.timeout_add(5000, self.checkNetwork)
        #self.isFullScreen = True
        
        self.sound.bip(1)
        
    def checkSettings(self):
        if config.has_option("SETTINGS", "devicename"):
            self.deviceName = str(config["SETTINGS"]["devicename"])
        else:
            config["SETTINGS"]["devicename"] = "Device 1"
            config.write(open("defaults.ini", "w"))
        
        if config.has_option("SETTINGS", "maxLogs"):
            self.maxLogs = int(str(config["SETTINGS"]["maxLogs"]))
        else:
            config["SETTINGS"]["maxLogs"] = "2000"
            config.write(open("defaults.ini", "w"))
        
        if config.has_option("SETTINGS", "autoDel"):
            pass
        else:
            config["SETTINGS"]["autoDel"] = "0"
            config.write(open("defaults.ini", "w"))
            
        if config.has_option("STATUS", "laststatus"):
            pass
        else:
            config["STATUS"]["laststatus"] = "IN"
            config.write(open("defaults.ini", "w"))
        
        if config.has_option("STATUS", "verifytime"):
            pass
        else:
            config["STATUS"]["verifytime"] = "1"
            config.write(open("defaults.ini", "w"))

    def checkNetwork(self):
        if Network.getIpAddress() == None:
            
            return True
        else:
            thread = threading.Thread(target = self.run_rest_api)
            thread.daemon = True
            thread.start()
            return False
    
    def run_rest_api(self):
        print("run server in background")
        from restapi import runserver 
        runserver()

            
    def wifiPressed(self,button):
        #WifiWindowController()
        pass

    def usersMenuPressed(self,button,event):
        self.notebook.set_current_page(2)
        
    def selectUserTable(self,selection):
        model,iterator = self.selectionUser.get_selected()
        if iterator == None:
            return
        #print("SELEZIONATO DA FUNC " + str(model[iterator][1]))
        self.userIdToEdit = model[iterator][3]
        self.notebook.set_current_page(5)
        
    def exitNewUserPressed(self,button):
        self.notebook.set_current_page(2)
                           
    def newUserPressed(self,button):
        self.userIdToEdit = None
        self.notebook.set_current_page(5)

    def deleteUserPressed(self,button):
        if self.userIdToEdit == None:
            return
        self.funcToExecuteOnConfirm = self.deleteUser
        res = DataManager().get_object_for_id("users",self.userIdToEdit)[0]
        
        self.showAlertPanel("Delete " + res["name"] + " , ID:  " + str(res["id_card"]) + " ?",2, buttonVisible=True)
        
    def deleteUser(self):
        self.funcToExecuteOnConfirm = None
        if self.userIdToEdit == None:
            return
        resUser = DataManager().delete("users",self.userIdToEdit)
        
        logsToDelete = DataManager().get_node("logs", {"user_ref" : str(self.userIdToEdit)})
        
        resLogs = None
        for row in logsToDelete["logs"]:
            resLogs = DataManager().delete("logs", row["id"])
        
        self.userIdToEdit = None
        if resUser["result"] == True:
            self.showAlertPanel("User Deleted !",2)
        

        
    def pageChanged(self,notebook,grid,pageIndex):
        self.window.fullscreen()
        users = DataManager().get_node("users")
        self.builder.get_object("labelDownload").set_text("-")
        if pageIndex == 1:#menu
            self.managerRun = False
            self.builder.get_object("labelMenuAlert").set_text("-")
            
        if pageIndex == 0:#homepage
            #self.builder.get_object("box2").connect("key-press-event", self.exitMenuPressed)
            self.startClock()

        elif pageIndex == 2: #user table page
            self.builder.get_object("barLoadUsers").set_visible(True)
            userModel.clear()
            if len(users["users"]) == 0:
                val = 1
            else:
                val = 1 / len(users["users"])
            currVal = val
            for user in users["users"]:
                userName = user["name"]
                if len(userName) > 20:
                    userName = userName[0:20] + ".."
                userModel.append([user["id_card"],userName,user["group"],user["id"]])
                currVal = currVal + val
                self.updateLoadUsersBar(currVal)
            self.selectionUser.unselect_all()
            self.builder.get_object("barLoadUsers").set_visible(False)
            
        elif pageIndex == 5: #new user
            self.builder.get_object("labelUserMessage").set_label("")
            if self.userIdToEdit != None:
                self.builder.get_object("buttonViewUserLogs").set_visible(True)
                self.builder.get_object("buttonDeleteUser").show()
                userToEdit = DataManager().get_object_for_id("users",self.userIdToEdit)
                if "error" in userToEdit:
                    self.userIdToEdit = None
                    return
                self.builder.get_object("fieldName").set_text(userToEdit[0]["name"])
                self.spinButtonId.set_value(userToEdit[0]["id_card"])
                self.builder.get_object("fieldCardCode").set_text(userToEdit[0]["card_code"])
                if userToEdit[0]["group"] == "user":
                    self.builder.get_object("labelButtonGroup").set_text("user")
                else:
                   self.builder.get_object("labelButtonGroup").set_text("manager")
                return
            #new user
            self.builder.get_object("buttonViewUserLogs").set_visible(False)
            self.builder.get_object("buttonDeleteUser").hide()
            self.builder.get_object("fieldName").set_text("")
            self.builder.get_object("fieldCardCode").set_text("")
            ids = self.getDeniedId()
            if len(ids) != 0:
                self.spinButtonId.set_value(max(ids) + 1)
            else:
                self.spinButtonId.set_value(1)
                
        elif pageIndex == 6: #logs
           pass
            
        elif pageIndex == 4: #settings
            
            self.spinbuttonVerify.set_value(self.reVerifyMin)
            self.builder.get_object("fieldDeviceName").set_text(config["SETTINGS"]["devicename"] )
            self.builder.get_object("spinButtonMaxLogs").set_value(self.maxLogs)
            switch = self.builder.get_object("switchAutoDelete")
            state = config["SETTINGS"]["autoDel"]
            if state == "1":
                switch.set_active(True)
            else:
                switch.set_active(False)
            
        elif pageIndex == 3: #network info
            ip = Network.getIpAddress()
            if ip == None:
                ip = "No Network"
            mac = Network.getMacAddress()
            if mac == None:
                mac = ip
            self.builder.get_object("labelIp").set_label(ip)
            self.builder.get_object("labelMac").set_label(mac)

        elif pageIndex == 8: #usb
            self.builder.get_object("progressBar").set_visible(False)
            self.builder.get_object("labelDownload").set_text("--")
            self.builder.get_object("progressBar").set_fraction(0)
            mounted = subprocess.check_output(["ls","/media/pi/"]).decode("unicode_escape").split("\n")
            mounted = list(filter(None, mounted))
            print(mounted)
            if len(mounted) == 0:
                self.mountedUsb = []
                self.builder.get_object("labelUsb").set_text("No Usb Devices")
                pass
            else :
                self.mountedUsb = mounted
                self.currentUsbInd = 0
                self.builder.get_object("labelUsb").set_text(self.mountedUsb[self.currentUsbInd])
            
    def updateLoadUsersBar(self, currVal):
        self.builder.get_object("barLoadUsers").set_fraction(currVal)
        while Gtk.events_pending(): Gtk.main_iteration()

    def downloadAllLogsPressed(self,button):
        logs = DataManager().get_node("logs")
        if "error" in logs.keys():
            self.showAlertPanel("No Logs to Save !",8)
            return
        if len(logs["logs"]) == 0:
            self.showAlertPanel("No Logs to Save !",8)
            return
        self.startDownload(logs)
            

    def downloadNewLogsPressed(self,button):
        logs = DataManager().get_node("logs",{"downloaded" : "0"})
        if "error" in logs.keys():
            self.showAlertPanel("No Logs to Save !",8)
            return
        if len(logs["logs"]) == 0:
            self.showAlertPanel("No Logs to Save !",8)
            return
        self.startDownload(logs)
        
    def startDownload(self, logs):
        self.builder.get_object("progressBar").set_visible(True)
        self.builder.get_object("labelDownload").set_text("Wait ...")
        self.builder.get_object("buttonSaveAllLogs").set_sensitive(False)
        self.builder.get_object("buttonSaveNewLogs").set_sensitive(False)
        self.builder.get_object("arrowButton").set_sensitive(False)
        self.builder.get_object("arrowButton1").set_sensitive(False)
        thread5 = threading.Thread(target = self.createCsv, args=[logs])
        thread5.daemon = True
        thread5.start()
                           
    def createCsv(self,logs):
        count=len(logs["logs"])
        frac = 1 / count
        fracVal = frac
        mountedUrl = "/media/pi/" + self.mountedUsb[self.currentUsbInd]
        filename = "Logs_" + datetime.now(get_localzone()).strftime('%d-%m-%Y_%H-%M-%S') + ".csv"
        for row in logs["logs"]:
            if "downloaded" in row: del row["downloaded"]
        if not os.path.exists(mountedUrl + "/LogData"):
            os.makedirs(mountedUrl + "/LogData")
        with open(mountedUrl +"/LogData/" + filename, "w+") as f:
            dictWriter = csv.DictWriter(f,["Name", "UID","DateTime","Status"])
            dictWriter.writeheader()
            for row in logs["logs"]:
                user = DataManager().get_object_for_id("users",row["user_ref"])
                if len(user) > 1 :
                    self.showAlertPanel("INTERNAL ERROR !",1)
                    return
                if len(user) == 0:
                    self.showAlertPanel("ERROR: some user not found !",1)
                    return
                name = user[0]["name"]
                uid = user[0]["id_card"]
                DateTime = dateutil.parser.parse(row["dateTime"]).strftime('%Y/%m/%d %H:%M:%S')
                Status = row["status"]
                dictWriter.writerow({"Name":name,"UID":uid,"DateTime":DateTime,"Status":Status})
                DataManager().edit_row("logs",row["id"],{"downloaded" : "1"})
                fracVal = fracVal + frac
                GObject.idle_add(self.upBar, fracVal)
        subprocess.call(["sudo","umount",mountedUrl])
        #self.showAlertPanel("successfully saved !\n \n extract the device",1)
        GObject.idle_add(self.finishDownloadUsb)
    
    def upBar(self, fracVal):
        self.builder.get_object("progressBar").set_fraction(fracVal)
        
        
    def finishDownloadUsb(self):
        self.builder.get_object("buttonSaveAllLogs").set_sensitive(True)
        self.builder.get_object("buttonSaveNewLogs").set_sensitive(True)
        self.builder.get_object("arrowButton").set_sensitive(True)
        self.builder.get_object("arrowButton1").set_sensitive(True)
        self.showAlertPanel("successfully saved !\n \n extract the device",1)

    def timeOutKey(self):
        self.keyTimeOut = True
        
    def timeoutRecord(self):
        self.builder.get_object("buttonRecord").set_sensitive(True)
        self.builder.get_object("labelButtonRecordCard").set_text("Record Card -->")
        self.builder.get_object("buttonSaveUser").grab_focus()
        #print("scaduro")

    def recordCardPressed(self,button):
        self.builder.get_object("labelUserMessage").set_label("")
        self.builder.get_object("fieldCardCode").grab_focus()
        self.builder.get_object("fieldCardCode").set_text("")
        self.builder.get_object("buttonRecord").set_sensitive(False)
        self.builder.get_object("labelButtonRecordCard").set_text("PRESENT CARD !")
        GObject.timeout_add(4000, self.timeoutRecord)

    def keyPressedInCardField(self,widget,event):
        if self.builder.get_object("fieldCardCode").get_text() != "":
            self.builder.get_object("fieldCardCode").set_text("")
        result = self.keyPressed(event.string)
        if result != None:
            self.sound.bip(1)
            #print("arrivato in card " + result)
            self.builder.get_object("fieldCardCode").set_text(result)
            self.builder.get_object("buttonSaveUser").grab_focus()
            self.builder.get_object("buttonRecord").set_sensitive(True)
            self.builder.get_object("buttonRecord").set_label("Record Card")
        
    def winKeyPress(self,widget,event):
        if self.notebook.get_current_page() != 0:
            return
        result = self.keyPressed(event.string)
        if result != None:
            #print("arrivato in home " + result)
            r = DataManager().get_node("users")
            if "error" in r:
                self.sound.bip(2)
                self.showHomeMessage("ERROR !")
                return
                
            if self.managerRun == True:  #non devo timbrare
                for item in r["users"]:
                    if "group" in item:
                        if item["group"] == "manager":
                            if item["card_code"] == result:
                                self.notebook.set_current_page(1)
                                self.sound.bip(1)
                                return
                self.showAlertPanel("PERMISSION DENIED !", 0)
                self.sound.bip(2)
            else: #in questo caso devo timbrare
                logs = DataManager().get_node("logs")
                if len(logs["logs"]) >= self.maxLogs:
                    if config["SETTINGS"]["autoDel"] == "0":
                        self.showAlertPanel("ERROR !\nREACHED MAX NUMBER OF LOGS !", 0)
                        self.sound.bip(2)
                        return
                    else:
                        thread = threading.Thread(target = self.deleteOldLogs)
                        thread.daemon = True
                        thread.start()
                trovato = 0
                lastLog = None
                lastTime = datetime.strptime('1975', '%Y')
                for item in r["users"]:
                    if item["card_code"] == result:
                        trovato = 1
                        #time = dateutil.parser.parse(item["dateTime"])
                        userId = item["id"]
                        if self.reVerifyMin != 0:
                            for log in logs["logs"]:
                                if log["user_ref"] == userId:
                                    time = dateutil.parser.parse(log["dateTime"])
                                    maxTime = time + timedelta(seconds=(self.reVerifyMin * 60))
                                    if lastLog == None:
                                        lastLog = log
                                    #lastTime = dateutil.parser.parse(log["dateTime"])
                                    if time > lastTime:
                                        lastLog = log
                                        lastTime = time
                                    if datetime.now() < maxTime:
                                        self.sound.bip(2)
                                        self.showHomeMessage("ERROR : Already Logged ! wait " + str(self.reVerifyMin) + "Min.")
                                        return

                        stat = config["STATUS"]["lastStatus"]
                        
                        if lastLog != None:
                            if lastLog["status"] == stat:
                                self.showHomeMessage("ERROR : Already staus " + stat + " !")
                                self.sound.bip(2)
                                return
                        
                        self.sound.bip(1)
                        logToSave = {"downloaded" : "0", "user_ref" : item["id"], "status": stat, "dateTime": datetime.now().isoformat()}
                        DataManager().add_row("logs",logToSave)
                        name = item["name"]
                        idCard = item["id_card"]
                        self.showHomeMessage("LOGGED " + stat + " , " + name + " , ID: " + str(idCard) )
                        return
                        
                if trovato == 0:
                    self.sound.bip(2)
                    self.showHomeMessage("ERROR: User Not Exist !")
                    
    def showHomeMessage(self, message):
        if hasattr(self,"messageTimeOut"):
                GObject.source_remove(self.messageTimeOut)
        self.builder.get_object("labelMessage").set_label(message)
        self.messageTimeOut = GObject.timeout_add(5000, self.clear_message)

    def clear_message(self):
        self.builder.get_object("labelMessage").set_label("--")
            
    def keyPressed(self,character):
        #print("KEYPRESSED")
        if hasattr(self, "keyClock"):
            GObject.source_remove(self.keyClock)
        self.keyClock = GObject.timeout_add(200, self.timeOutKey)
        if self.keyTimeOut == False:
            if character != "\r":
                self.readCardString += character
            else:
                if len(self.readCardString) == 10:
                    GObject.source_remove(self.keyClock)
                    self.keyTimeOut = False
                    result = self.readCardString
                    self.readCardString = ""
                    return result
                else:
                    self.readCardString = ""
                    GObject.source_remove(self.keyClock)
        else:
            self.keyTimeOut = False
            self.readCardString = ""
            
    def deleteOldLogs(self): 
        logs = DataManager().get_node("logs")["logs"]
        sortedLogs = sorted(logs, key= lambda x:dateutil.parser.parse(x["dateTime"]))  #la prima è la piu vecchia
        print("primo:" + logs[0]["dateTime"], "ultimo" + logs[len(logs) - 1]["dateTime"])
        totToDelete = len(logs) - (self.maxLogs + 1)
        if totToDelete <= 0:
            return
        count = 0
        for log in sortedLogs:
            DataManager().delete("logs", log["id"])
            print("cancellato " + log["dateTime"])
            count += 1
            if count == totToDelete:
                return
            
    def viewUserLogsPressed(self, button):
        if self.userIdToEdit == None:
            return
        userToEdit = DataManager().get_object_for_id("users",self.userIdToEdit)
        self.notebook.set_current_page(6)
        userName = userToEdit[0]["name"]
        if len(userName) > 12:
            userName = userName[0:12] + ".."
        self.builder.get_object("labelLogsMessage").set_text(userName)
        GObject.timeout_add(50, self.showLogs, userToEdit[0]["id_card"])
        self.userIdToEdit = None
        
        
    def saveUserPressed(self,button):
        self.builder.get_object("labelUserMessage").set_label("")
        name = self.builder.get_object("fieldName").get_text()
        cardCode = self.builder.get_object("fieldCardCode").get_text()
        group = self.builder.get_object("labelButtonGroup").get_text()
        if not name or not cardCode:
            self.builder.get_object("labelUserMessage").set_label("FIELD MISSING !")
            return
        if int(self.spinButtonId.get_value()) in self.getDeniedId():
            self.builder.get_object("labelUserMessage").set_label("ERROR : ID already exist !")
            #self.showAlertPanel("error : ID already exist !",5)
            return
        if cardCode in self.getDeniedCards():
            self.sound.bip(2)
            self.builder.get_object("labelUserMessage").set_label("ERROR : CARD already exist !")
            return
        userToSave = {"name": name,"card_code":cardCode,"last_status":"IN","group":group,"id_card":int(self.spinButtonId.get_value())}
        if self.userIdToEdit == None:
            DataManager().add_row("users",userToSave)
        else:
            DataManager().edit_row("users",self.userIdToEdit,userToSave)
        self.userIdToEdit = None
        self.showAlertPanel("User Saved !",2)
        
    def getDeniedId(self):
        users = DataManager().get_node("users")
        ids = []
        for user in users["users"]:
            if self.userIdToEdit != None:
                if not user["id"] == self.userIdToEdit:
                    ids.append(user["id_card"])
            else:
                ids.append(user["id_card"])
        return ids
    
    def getDeniedCards(self):
        users = DataManager().get_node("users")
        cards = []
        for user in users["users"]:
            if self.userIdToEdit != None:
                if not user["id"] == self.userIdToEdit:
                    cards.append(user["card_code"])
            else:
                cards.append(user["card_code"])
        return cards
    
    def getFreePressed(self,button):
        ids = self.getDeniedId()
        if len(ids) != 0:
            self.spinButtonId.set_value(max(ids) + 1)
        else:
            self.spinButtonId.set_value(1)

    def deleteAllLogsPressed(self,button,event):
        self.funcToExecuteOnConfirm = self.deleteLogs
        self.showAlertPanel("Delete these Logs ?",6, buttonVisible=True)
        
    def buttonConfirmPressed(self, button, event):
        if self.funcToExecuteOnConfirm == None:
            return
        else:
            self.funcToExecuteOnConfirm()

            
    def deleteLogs(self):
        for i,log in enumerate(logModel):
            res = DataManager().delete("logs",str(logModel[i][3]))
                
        self.funcToExecuteOnConfirm = None
        self.showAlertPanel("Logs Cancelled !",1)
            
    def showLogs(self, id=None):
        logModel.clear()
        self.builder.get_object("loadLogs").set_visible(True)
        nonSortedLogs = DataManager().get_node("logs")["logs"]
        logs = sorted(nonSortedLogs, key=lambda k: dateutil.parser.parse(k["dateTime"]), reverse=True)
        users = DataManager().get_node("users")
        if len(logs) == 0:
            val = 1
        else:
            val = 1 / len(logs)
        currFrac = val
        if id == None:
            for log in logs:
                currFrac = currFrac + val
                self.incrementProgressLogs(currFrac)
                r = [r for r in users["users"] if r["id"] == log["user_ref"]]
                if len(r) != 1:
                    r = []
                    r.append({"id_card":"Unknown"})
                logModel.append([str(r[0]["id_card"]),dateutil.parser.parse(log["dateTime"]).strftime('%d/%m/%Y %H:%M:%S'),log["status"],log["id"]])
                
        else:
            for log in logs:
                currFrac = currFrac + val
                self.incrementProgressLogs(currFrac)
                r = [r for r in users["users"] if r["id"] == log["user_ref"]]
                if len(r) == 1:
                    if r[0]["id_card"] == id:
                        logModel.append([str(r[0]["id_card"]),dateutil.parser.parse(log["dateTime"]).strftime('%d/%m/%Y %H:%M:%S'),log["status"],log["id"]])
        self.builder.get_object("loadLogs").set_visible(False)
        
    def incrementProgressLogs(self, frac):
        bar = self.builder.get_object("loadLogs")
        #bar.window.process_updates(True)
        bar.set_fraction(frac)
        while Gtk.events_pending(): Gtk.main_iteration()
        
    def maxLogsValueChange(self, spinner):
        self.maxLogs = spinner.get_value_as_int()
        config["SETTINGS"]["maxLogs"] = str(self.maxLogs)
        self.saveConfig()
    
    def activateAutoDelSwitch(self, switchButton, event):
        if switchButton.get_active():
            config["SETTINGS"]["autoDel"] = "1"
            self.saveConfig()
        else:
            config["SETTINGS"]["autoDel"] = "0"
            self.saveConfig()
    
    def spinnerReVerifyChange(self,spinner):
        #print(str(spinner.get_value_as_int()))
        val = spinner.get_value_as_int()
        config["STATUS"]["verifytime"] = str(val)
        self.saveConfig()
        self.reVerifyMin = int(val)
        
    def changeGroupPressed(self, button):
        if self.builder.get_object("labelButtonGroup").get_text() == "user":
            print("uno")
            self.builder.get_object("labelButtonGroup").set_text("manager")
        else:
            print("due")
            self.builder.get_object("labelButtonGroup").set_text("user")
        
         
    def logsMenuPressed(self,button):
        self.notebook.set_current_page(6)
        self.builder.get_object("labelMenuAlert").set_text("Wait ...")
        self.builder.get_object("labelLogsMessage").set_text("All Logs")
        GObject.timeout_add(50, self.showLogs)

    def downloadPressed(self,button):
        self.notebook.set_current_page(8)
        
    def settingsPressed(self,button):
        self.notebook.set_current_page(4)
        
    def exitSettingsPressed(self, button):
        name = self.builder.get_object("fieldDeviceName").get_text()
        if name != "":
            config["SETTINGS"]["devicename"] = name
            self.saveConfig()
        self.notebook.set_current_page(1)
            
            

    def exitPressed(self,button, event):
        self.notebook.set_current_page(1)

    def exitMenuPressed(self, button, event):
        self.notebook.set_current_page(0)

        
    def inPressed(self,button):
        self.labelInOut.set_label("IN")
        config["STATUS"]["lastStatus"] = "IN"
        self.saveConfig()

    def outPressed(self,button):
        self.labelInOut.set_label("OUT")
        config["STATUS"]["lastStatus"] = "OUT"
        self.saveConfig()

    def menuButtonPressed(self, button, event):
        r = DataManager().get_node("users")
        if "error" in r:
            self.notebook.set_current_page(1)
            return
        
        for item in r["users"]:
            if "group" in item:
                if item["group"] == "manager":
                    self.labelOrario.set_label("Manager ?")
                    self.managerRun = True
                    GObject.timeout_add(6500, self.end_manager_time)
                    return
        self.notebook.set_current_page(1)
        
    def end_manager_time(self):
        print("endmanager")
        self.managerRun = False
        self.startClock()
        
    def networkInfoPressed(self,button):
        self.notebook.set_current_page(3)

    def tick(self):
        #self.window.unmaximize()
        #if self.notebook.get_current_page() != 0:
            #return True
        if self.managerRun == False:
            self.labelOrario.set_label(datetime.now(get_localzone()).strftime('%H:%M:%S'))
        
        if Network.isWifiNetwork:
            sigString = Network.getWifiPower()
            if sigString == None:
                sigString = "No WiFi"
            self.builder.get_object("labelSignal").set_label(sigString)
        else:
            self.builder.get_object("labelSignal").set_label("")
        return True #in modo che ripeta
        
    
    def startClock(self):
        self.clock = GObject.timeout_add(200, self.tick)

    def saveConfig(self):
        with open("defaults.ini" ,"w") as fileConf:
            config.write(fileConf)
            
    def treeViewGrabFocus(): #override
        model,iterator = self.selectionUser.get_selected()
        Gtk.TreeView.grab_focus(self.tableViewUser)
        if itetrator is None:
            self.selectionUser.unselect_all()
            
    def timeOutAlert(self,page):
        self.funcToExecuteOnConfirm = None
        self.notebook.set_current_page(page)
        
        
    def showAlertPanel(self,message,prevPage, buttonVisible=False):
        if buttonVisible == True:
            self.builder.get_object("buttonConfirm").set_visible(True)
        else:
            self.builder.get_object("buttonConfirm").set_visible(False)
        if prevPage == None:
            prev = self.notebook.get_current_page()
        else:
            prev = prevPage
        self.notebook.set_current_page(7)
        self.builder.get_object("labelMessag").set_label(message)
        GObject.timeout_add(3500, self.timeOutAlert,prev)
        
    def quitPressed(self,button):
        if self.isFullScreen == True:
            self.window.unfullscreen()
            self.isFullScreen = False
            #self.builder.get_object("buttonReduce").set_label("Full Scr")
        else:
            self.window.fullscreen()
            self.isFullScreen = True
            #self.builder.get_object("buttonReduce").set_label("Reduce")

    def winClosed(self,button, event):
        GPIO.output(35, GPIO.LOW)
        
    def avantiUsbPressed(self,button):
        #print("avanti")
        if len(self.mountedUsb) == 0 or len(self.mountedUsb) == 1:
            return
        if self.currentUsbInd < (len(self.mountedUsb) - 1):
            self.currentUsbInd += 1
            self.builder.get_object("labelUsb").set_text(self.mountedUsb[self.currentUsbInd])
                
        

    def indietroUsbPressed(self,button):
        #print("indietro")
        if len(self.mountedUsb) == 0 or len(self.mountedUsb) == 1:
            return
        if self.currentUsbInd > 0:
            self.currentUsbInd -= 1
            self.builder.get_object("labelUsb").set_text(self.mountedUsb[self.currentUsbInd])
            
    
        
        
def startApp():
    win = HomeWindowController()
    GObject.threads_init()
    win.startClock()
    Gtk.main()
