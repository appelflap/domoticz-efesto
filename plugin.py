# Efesto Python Plugin for Domoticz
#
# Author: Appelflap (Albert Drenth) <albert@appelflap.me>
#
# Version 0.1.4 (2018-11-21) : Create devices, calls, update values, update plugin HTML
#         0.1.3 (2018-11-20) : Translated my code Lua -> Python 
#         0.1.2 (2018-11-20) : Basic structure, connector
# 
#                              TODO:
#                              - minimum run time ?? At least make it possible
#                              - fail safe (temp in home > setpoint+2 and status == 4, turn it off?)
#                              - notifications
#                              - debug only if selected in config
#                              - example Lua code to connect to Tado
#                              - figure out the alarm modes/codes of the device
#                              - add the optional notifications when switching?
#
"""
<plugin key="BasePlug" name="Efesto Heater Control" author="appelflap" version="0.1.4" wikilink="http://www.domoticz.com/wiki/plugins/efesto.html" externallink="https://github.com/appelflap/domoticz-efesto">
    <description>
        <h2>Efesto Heater Plugin</h2><br/>
        Overview+.
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Automatically makes devices for your heater</li>
            <li>Sets power setting (1-5)</li>
            <li>Recognizes working states {"OFF","START","LAOD PELLET","FLAME LIGHT","WORK"...}</li>
            <li>TODO: Recognize Alarm states</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Heater - On/Off</li>
            <li>Power - Percentage</li>
            <li>Status - String</li>
            <li>Alarm - On/Off (read-only)</li>
            <li>Air Thermostat - Thermostat temperature setpoint</li>
            <li>Air Temperature - Room temperature near heater</li>
            <li>Water Thermostat - Thermostat temperature setpoint (if available in Heater)</li>
            <li>Water Temperature - Water output temperature (if available in Heater)</li>
            <li>Smoke Temperature - Output temperature of heater</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options+.
    </description>
    <params>
        <param field="Address" label="Host URL" width="200px" required="true" default="http://amg.efesto.web2app.it"/>
        <param field="Mode1" label="Check Interval(seconds)" width="75px" required="true" default="60"/>
        <param field="Mode2" label="Notifications" width="75px">
            <options>
                <option label="Notify" value="Notify"/>
                <option label="Disable" value="Disable"  default="true" />
            </options>
        </param>
        <param field="Mode3" label="HeaterId" width="150px" required="false" default="FFFFFFFFFFFF"/>
        <param field="Mode4" label="SessionId" width="150px" required="false" default="qwertyuiopasdfghjklzxcvbnm"/>
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import time

from datetime import datetime, timedelta

class BasePlugin:
    enabled = False
    statusLang = {"OFF","START","LAOD PELLET","FLAME LIGHT","WORK","CLEANING FIRE-POT","CLEANING FINAL","ECO-STOP","?","NO FIRE?","?","?","?","?","?","?","?","?","?","?"}
    httpConn = None
    start = 0
    
    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        
        # set value to create devices after first fetch
        self.start = 1
        
        self.pollInterval = int(Parameters["Mode1"])  #Time in seconds between two polls
        self.heaterId = Parameters["Mode3"]
        self.sessionId = Parameters["Mode4"]
        self.remember = Parameters["Mode5"]
        
        if mid(Parameters["Address"],0,7) == "http://":
            self.port = 80
            self.host = Parameters["Address"][7:]
        elif mid(url,0,8) == "https://"  :
            self.port = 443
            self.host = Parameters["Address"][8:]
        else:
            Domoticz.Error("URL Prefix is wrong: 'http://' or 'https://' required.")
            return
            
        self.headers = {
            'Host': self.host, 
            'Accept': 'application/json; q=0.01',
            'Origin': self.protocol+'://'+efestoHost, 
            'Referer': self.protocol+'://'+efestoHost+'/en/heaters/action/manage/heater/'+efestoHeaterId+'/',
            'Cookie': 'PHPSESSID='+efestoSessionId+'; language=en'
        }
        self.url = self.protocol+'://'+efestoHost+'/en/ajax/action/frontend/response/ajax/'
                    
        Domoticz.Heartbeat(self.pollInterval)

    def onStop(self):
        Domoticz.Log("Plugin is stopping")
        Domoticz.Debugging(0)

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("Efesto connected successfully")
            sendData = { 'Verb': 'POST', 'URL': self.url, 'Headers': self.headers}
            Connection.Send(sendData) # Jumps to onMessage
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)
        

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")
        DumpHTTPResponseToLog(Data)
        
        strData = Data["Data"].decode("utf-8", "ignore")
        Status = int(Data["Status"])
        LogMessage(strData)

        if (Status == 200):
            Domoticz.Log("Good Response received from Efesto. Parsing data...")
            Response = json.loads(strData)
            
            if (Response["status"] != 0):
                Domoticz.Log("Warning: API says status is not ok: "+Response["status"])
            
            self.message = Response["message"]
                
            if (Response["method"] == "get-state"):
                # See efestoResponse.json
                
                createDevices()
                
                Domoticz.Debug("get-state recieved")
                if (Message == None):
                    # euh... do something?
                    return
                if(self.message["deviceStatus"] == 0 or self.message["deviceStatus"] == 6): 
                    self.heater = 0
                else:
                    self.heater = 1
                    
                UpdateDevice(1, 0, str(self.heater))
                UpdateDevice(2, 0, str(round(self.message["lastSetPower"])*20))
                UpdateDevice(3, 0, self.statusLang[self.message["deviceStatus"]]+" ("+self.message["deviceStatus"]+")")
                UpdateDevice(4, 0, self.message["isDeviceInAlarm"])
                UpdateDevice(5, 0, str(round(self.message["airTemperature"], 1)))
                UpdateDevice(6, 0, str(round(self.message["lastSetAirTemperature"], 1)))
                UpdateDevice(7, 0, str(round(self.message["smokeTemperature"], 1)))
                UpdateDevice(8, 0, str(round(self.message["waterTemperature"], 1)))
                UpdateDevice(9, 0, str(round(self.message["lastSetWaterTemperature"], 1)))
                
            elif (Response["method"] == "heater-on"):
                Domoticz.Debug("heater-on ack recieved")
                
            elif (Response["method"] == "heater-off"):
                Domoticz.Debug("heater-off ack received")
                
            elif (Response["method"] == "write-parameters-queue"):
                Domoticz.Debug("write-parameters-queue ack recieved")
                # {"status":0,"message":{"set-power":0},"method":"write-parameters-queue"}
                if "set-power" in self.message:
                    Domoticz.Debug("set-power ack recieved")
                if "set-air-temperature" in self.message:
                    Domoticz.Debug("set-air-temperature ack recieved")
                if "set-water-temperature" in self.message:
                    Domoticz.Debug("set-water-temperature ack recieved")
            
            self.httpConn.Disconnect()
        elif (Status == 302):
            Domoticz.Log("Efesto Moved?")
            sendData = { 'Verb' : 'POST', 'URL'  : Data["Headers"]["Location"], 'Headers' : self.headers }
            Connection.Send(sendData)
        elif (Status == 400):
            Domoticz.Error("Efesto returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("Efesto returned a Server Error.")
        else:
            Domoticz.Error("Efesto returned a status: "+str(Status))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        
        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()

        if (self.httpConn.Connected() == False):
            self.httpConn = Domoticz.Connection(Name=self.protocol+" Test", Transport="TCP/IP", Protocol="JSON", Address=self.host, Port=self.port)
            self.httpConn.Connect() # Jumps to onConnect() ?

        if (action == 'On'):
            if (Unit == 1):
                sendData = { 'Verb': 'POST', 'URL': self.url, 'Headers': self.headers, 'Data': "method=heater-on&params=1&device="+self.heaterId}
                Connection.Send(sendData) # Also activates onMessage
        elif (action == 'Off'):
            sendData = { 'Verb': 'POST', 'URL': self.url, 'Headers': self.headers, 'Data': "method=heater-off&params=1&device="+self.heaterId}
            Connection.Send(sendData) # Also activates onMessage
        elif (action == 'Set'):
            if (Unit == 2):
                sendData = { 'Verb': 'POST', 'URL': self.url, 'Headers': self.headers, 'Data': "method=write-parameters-queue&params=set-power%3D"+str(round(Level/20,0))}
                Connection.Send(sendData) # Also activates onMessage
            elif (Unit == 5):
                sendData = { 'Verb': 'POST', 'URL': self.url, 'Headers': self.headers, 'Data': "method=write-parameters-queue&params=set-air-temperature%3D"+str(Level)}
                Connection.Send(sendData) # Also activates onMessage
            elif (Unit == 8):
                sendData = { 'Verb': 'POST', 'URL': self.url, 'Headers': self.headers, 'Data': "method=write-parameters-queue&params=set-water-temperature%3D"+str(Level)}
                Connection.Send(sendData) # Also activates onMessage
            else:
                Domoticz.Log("Value of Unit "+str(Unit)+" can't be set")

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        
        self.httpConn = Domoticz.Connection(Name=self.protocol+" Test", Transport="TCP/IP", Protocol="JSON", Address=self.host, Port=self.port)
        self.httpConn.Connect() # Jumps to onConnect()
        
        Domoticz.Heartbeat(self.pollInterval)

    def createDevices():
        Domoticz.Log("createDevices called")
        if(self.start):
            if 1 not in Devices:
                Domoticz.Device(Name="Heater", Unit=1, TypeName="Switch", Used=1).Create()
            if 2 not in Devices:
                # Value is 1-5, but will be saved as Percentage
                Domoticz.Device(Name="Power", Unit=2, TypeName="Percentage", Used=1).Create()
            if 3 not in Devices:
                Domoticz.Device(Name="Status", Unit=3, TypeName="Text", Used=1).Create()
            if 4 not in Devices:
                Domoticz.Device(Name="Alarm", Unit=4, TypeName="Switch", Used=1).Create()
            if 5 not in Devices:
                Domoticz.Device(Name="Air Thermostat", Unit=5, Type=242, Subtype=1, Used=1).Create()
            if 6 not in Devices:
                Domoticz.Device(Name="Air Temperature", Unit=6, TypeName="Temperature", Used=1).Create()
            if 7 not in Devices:
                Domoticz.Device(Name="Smoke Temperature", Unit=7, TypeName="Temperature", Used=1).Create()
            if(8 not in Devices and self.message["canSetWaterTemperature"] != 0):
                Domoticz.Device(Name="Water Thermostat", Unit=8, TypeName="Temperature", Used=1).Create()                
            if(9 not in Devices and self.message["waterTemperature"] != 255):
                Domoticz.Device(Name="Water Temperature", Unit=9, TypeName="Temperature", Used=1).Create()
        
    #
    # Parse an int and return None if no int is given
    #

    def parseIntValue(self, s):

        try:
            return int(s)
        except:
            return None

    #
    # Parse a float and return None if no float is given
    #

    def parseFloatValue(self, s):

        try:
            return float(s)
        except:
            return None
    
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
    
# Update Device into database
def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or AlwaysUpdate == True:
            Devices[Unit].Update(nValue, str(sValue))
            Domoticz.Log("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
    return
