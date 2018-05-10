# Domoticz Python Plugin to monitor router for presence/absence of wifi devices without pinging them (pinging can drain your phone battery).
#
# Author: ESCape
#
"""
<plugin key="idetect" name="iDetect Wifi presence detection " author="ESCape" version="0.3.0">
	<description>
		<h2>Presence detection by router</h2><br/>
		<h3>Authentication settings</h3>
		<ul style="list-style-type:square">
			<li>Leave the password field empty to use ssh public key authentication.</li>
			<li>SSH key authentication must be configured on the router and on the OS (linux) using ~/.ssh/id_rsa.pub for the user running domoticz.</li>
			<li>If you enter a password in the password field, then the plugin will use password authentication. Make sure you have installed sshpass (sudo apt-get install sshpass). This is much easier than key authentication, but less secure. Your password wil be stored in the Domoticz database in plain text and is readable on the settings page.</li>
		</ul>
		<h3>Behaviour settings</h3>
		<ul style="list-style-type:square">
			<li>Enter mac addresses to monitor in the format phone1=F1:2A:33:44:55:66,phone2=B9:88:77:C6:55:44 (and more, separated by comma).
			The name should be short and descriptive. It  will be used as the identifying deviceID and the initial device name. You can change the devices name after it has been created.</li>
			<li>'remove obsolete' gives you a choice to automatically delete devices that are no longer in de above list of mac-addresses OR to show them as timedout.</li>
			<li>The grace period controls after how long phones are shown as absent (to deal with temporarily dropped connections).</li>
			<li>The plugin will automatically determine which command to use on the router for which wireless interfaces. This is only tested on a Asus router running asuswrt (ac86u), but should make the plugin compatible with other routers and firmwares.</li>
		</ul>
	</description>
	<params>
		<param field="Address" label="Wifi router IP Address" width="200px" required="true" default="192.168.0.1"/>
		<param field="Username" label="Username" width="200px" required="true" default=""/>
		<param field="Password" label="Password" width="200px" required="false" default="" password="true"/>
		<param field="Mode1" label="MAC addresses te monitor" width="500px" required="true" default="phone1=A1:B1:01:01:01:01,phone2=C2:D2:02:02:02:02"/>
		<param field="Mode6" label="Remove obsolete" width="250px">
			<options>
				<option label="Delete obsolete devices" value="True"/>
				<option label="Show obsolete devices as unavailable" value="False"/>
			</options>
		</param>
		<param field="Mode2" label="Interval (sec)" width="75px" required="true" default="10"/>
		<param field="Mode3" label="Grace period (sec)" width="75px" required="true" default="30"/>
		<param field="Mode5" label="Debug mode" width="250px">
			<options>
				<option label="Off" value="False" default="True"/>
				<option label="On" value="True"/>
			</options>
		</param>

	</params>
</plugin>
"""

import Domoticz
from datetime import datetime, timedelta
import subprocess

class BasePlugin:

	def __init__(self):
		self.monitormacs = {}
		self.graceoffline = 0
		self.timelastseen = {}
		self.errorcount = 0
		return
		
	def getfromssh(self, host, user, passwd, routerscript, alltimeout=2, sshtimeout=1):
		if self.errorcount > 5:
			Domoticz.Error("Temporarily limiting the polling frequency to twice a minute after encountering more than 5 (ssh) errors in a row.")
			Domoticz.Heartbeat(30)
		if passwd:
			Domoticz.Debug("Using password instead of ssh public key authentication (less secure!)")
			cmd =["sshpass", "-p", passwd, "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=" + str(sshtimeout), user+"@"+host, routerscript]
		else:
			Domoticz.Debug("Using ssh public key authentication (~/.ssh/id_rsa.pub) for OS user running domoticz.")
			cmd =["ssh", "-o", "ConnectTimeout=" + str(sshtimeout), user+"@"+host, routerscript]
			if self.debug and self.errorcount != 0:
				try:
					osuser=subprocess.run("whoami", stdout=subprocess.PIPE, timeout=1)
					runasuser = osuser.stdout.decode("utf-8").strip()
					Domoticz.Log("The OS user profile running domoticz is:	" + str(runasuser))
				except:
					Domoticz.Debug("Could not detemine the user profile running Domoticz")
		try:
			Domoticz.Debug("Fetching data from router using ssh")
			Domoticz.Debug("command: " + str(cmd))
			completed=subprocess.run(cmd, stdout=subprocess.PIPE, timeout=alltimeout)
			Domoticz.Debug("Returncode ssh command: " + str(completed.returncode))
			Domoticz.Debug("Output from router: " + str(completed.stdout))
			if completed.returncode == 0 and completed.stdout != "":
				if self.errorcount != 0:
					self.errorcount = 0
					Domoticz.Error("SSH connection restored. Resuming operation at set poll frequency.")
					Domoticz.Heartbeat(int(Parameters["Mode2"]))					
				return True, completed.stdout
			elif completed.stdout == "":
				Domoticz.Error("Router returned empty response. Returncode ssh: " + str(completed.returncode))
			elif completed.returncode == 5:
				Domoticz.Error("Router authentication failed")
			elif completed.returncode == 127:
				Domoticz.Error("Router rurned command nog found.")
				Domoticz.Error("Output from router: " + str(completed.stdout))
			elif completed.returncode == 130:
				Domoticz.Error("Router ssh command was interrupted.")
			else:
				Domoticz.Error("Router command failed with returncode: " + str(completed.returncode))
				Domoticz.Error("Raw data from router: " + str(completed.stdout))
			self.errorcount += 1
			return False, str(completed.returncode)
		except subprocess.TimeoutExpired:
			Domoticz.Error("SSH subprocess timed out")
			self.errorcount += 1
			return False, "Subprocess timed out"

	def routercommand(self, host, user, passwd):
		#The routerscript below will run on the router itself to determine which command and interfaces to use
		#Preferred method is 'wl' command, but this plugin can use 'arp' as fallback
		#The constructed command should return a clean list of mac addresses. One address per line in the format xx:xx:xx:xx:xx:xx.
		#Mac addresses from all known wireless interfaces should be included. Case doesn't matter, we'll take care of that when using the data.
		routerscript="""#!/bin/sh
					export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
					test=$(which wl > /dev/null 2>&1)
					if [ $? == 0 ]; then
							printf "wl@"
							for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep '^eth\|^wlan')
							do
									test=$(wl -i $iface assoclist > /dev/null 2>&1)
									if [ $? == 0 ]; then
											printf "$iface "
									fi
							done
							exit
					fi
					test=$(which iwinfo > /dev/null 2>&1)
					if [ $? == 0 ]; then
							printf "iwinfo@"
							for iface in $(iwinfo | cut -d ' ' -f1| tr ':' '\n' | grep '^eth\|^wlan')
							do
									test=$(iwinfo wlan0 assoclist > /dev/null 2>&1)
									if [ $? == 0 ]; then
											printf "$iface "
									fi
							done
							exit
					fi					
					test=$(which arp > /dev/null 2>&1)
					if [ $? == 0 ]; then
							printf "arp"
					fi"""	
		
		Domoticz.Debug("Checking router capabilities and wireless interfaces")
		success, sshdata=self.getfromssh(host, user, passwd, routerscript, alltimeout=4, sshtimeout=2)
		if success:
			gotinfo = sshdata.decode("utf-8").split("@")
			method = gotinfo[0]
			interfaces = gotinfo[-1].split()
			Domoticz.Debug("Parsed data from router: " + str(gotinfo))
			if method=="wl":
				Domoticz.Log("Using wl command on router (best method) for interfaces " + str(interfaces))
				pollscript="export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH"
				for knownif in interfaces:
					pollscript=pollscript + ";wl -i " + knownif + " assoclist | cut -d' ' -f2"
				pollscript=pollscript + ";exit"
			elif method=="iwinfo":
				Domoticz.Log("Using iwinfo command on router (best method) for interfaces " + str(interfaces))
				pollscript="export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH"
				for knownif in interfaces:
					pollscript=pollscript + ";iwinfo " + knownif + " assoclist | grep '^..:..:..:..:..:.. ' | cut -d' ' -f1"
				pollscript=pollscript + ";exit"				
			elif method=="arp":
				Domoticz.Log("wl command not available on router. Using arp instead (slower response to presence)")
				pollscript="export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH;arp -a | grep '..:..:..:..:..:..' | awk '{print $ 4}';exit"
			else:
				Domoticz.Error("Unable to construct router commandline for presence")
				pollscript = "none"
			Domoticz.Debug("Constructed this cmd for the router to poll for present phones: " + pollscript)
			return pollscript
		else:
			Domoticz.Error("Could not determine router capabilities")
			return "none"

	def activemacs(self, host, user, passwd, routerscript):
		Domoticz.Debug("Polling present phones from router")
		success, sshdata=self.getfromssh(host, user, passwd, routerscript)
		if success:
			list=[]
			for item in sshdata.splitlines():
				list.append(item.decode("utf-8").upper())
			return list
		else:
			Domoticz.Error("Failed to poll present phones from router")
			return None

	def updatestatus(self, id, onstatus):
		if onstatus:
			svalue = "On"
			nvalue = 1
		else:
			svalue = "Off"
			nvalue = 0
		if id not in Devices:
			Domoticz.Log("Device " + str(id) + " does not exist")
			return
		if Devices[id].nValue != nvalue or Devices[id].sValue != svalue:
			Devices[id].Update(nValue=nvalue, sValue=svalue)
			Domoticz.Debug("Changing device " + Devices[id].Name + " to " + svalue)
			
	def onStart(self):
		#setup debugging if enabled in settings
		if Parameters["Mode5"]=="True":
			Domoticz.Debugging(1)
			self.debug=True
		else:
			self.debug=False
			
		Domoticz.Debug("Debugging mode enabled")
		
		#prepare some variables and use the parameters from te settings page
		maclist={}
		devmacs=Parameters["Mode1"].replace(" ", "").split(",")
		for item in devmacs:
			try:
				name, mac =item.split("=")
				maclist.update({name.strip():mac.strip().upper()})
			except:
				Domoticz.Error("Invalid device/mac setting in: " + str(devmacs))
		self.monitormacs = maclist
		Domoticz.Debug("Monitoring " + str(self.monitormacs) + " for presence.")
		Domoticz.Heartbeat(int(Parameters["Mode2"]))
		self.graceoffline = int(Parameters["Mode3"])
		self.routerip = Parameters["Address"]
		self.routeruser = Parameters["Username"]
		self.routerpass = Parameters["Password"]
		self.individualswitches = True
		self.deleteobsolete = Parameters["Mode6"] == "True"
		#self.devnametoid={}
		self.devid2domid={}
		self.routercmdline = self.routercommand(self.routerip, self.routeruser, self.routerpass)

		#Select or create icons for devices 
		homeicon="idetect-home"
		uniticon="idetect-unithome"
		if homeicon not in Images: Domoticz.Image('ihome.zip').Create()
		homeiconid=Images[homeicon].ID
		if uniticon not in Images: Domoticz.Image('iunit.zip').Create()
		uniticonid=Images[uniticon].ID
		
		#Create "Anyone home" device
		if 1 not in Devices:
			Domoticz.Device(Name="Anyone", DeviceID="#Anyone", Unit=1, TypeName="Switch", Used=1, Image=homeiconid).Create()
			Domoticz.Log("Device created fot general/Anyone presence")
		
		#Find obsolete device units (no longer configured te be monitored)
		deletecandidates=[]
		for dev in Devices:
			if dev == 1:
				continue
			#Check if devices are still in use
			Domoticz.Debug("monitoring device: " + Devices[dev].Name)
			if Devices[dev].DeviceID in self.monitormacs: #prep for use
				Domoticz.Debug(Devices[dev].Name + " is stil in use")
				#self.devnametoid.update({Devices[dev].Name.split(" ")[-1]:dev})
				self.devid2domid.update({Devices[dev].DeviceID:dev})
			else: #delete device
				if dev != 1:
					if self.deleteobsolete:
						Domoticz.Log("deleting device unit: " + str(dev) + " named: " + Devices[dev].Name)
						deletecandidates.append(dev)
					else:
						Devices[dev].Update(nValue=0, sValue="Off", TimedOut=1)

		Domoticz.Debug("devid2domid: " + str(self.devid2domid))
		#Domoticz.Debug("devnametoid: " + str(self.devnametoid))
		Domoticz.Debug("monitormacs: " + str(self.monitormacs))

		for obsolete in deletecandidates:
			Devices[obsolete].Delete()

		#Check if there is a Domoticz device for the configured MAC address
		for friendlyid in self.monitormacs:
			if friendlyid not in self.devid2domid:
				Domoticz.Debug(friendlyid + " not in known device list")
				success=False
				for num in range(2,200):
					if num not in Devices:
						Domoticz.Log("creating device for " + friendlyid + " with unit id " + str(num)) 
						Domoticz.Device(Name=friendlyid, Unit=num, DeviceID=friendlyid, TypeName="Switch", Used=1, Image=uniticonid).Create()
						Devices[num].Update(nValue=0, sValue="Off")
						self.devid2domid.update({Devices[num].DeviceID:num})
						success=True
						break
				if not success:
					Domoticz.Error("No numers left to create device for " + friendlyid)

	def onHeartbeat(self):
		Domoticz.Debug("devid2domid: " + str(self.devid2domid))
		if self.routercmdline == "none":
			#something must have gone wrong while initializing the plugin. Let's try again and skip the detection this time. 
			Domoticz.Error("No usable commandline to check presence. Trying again to detect router capabilities.")
			Domoticz.Error("If you keep getting this message: check your (authentication) settings and router status.")
			Domoticz.Error("Make sure your router supports ssh and the commands used by this plugin. If this message persists disable the plugin (for now), or the plugin might flood the Domoticz eventsystem")
			self.routercmdline = self.routercommand(self.routerip, self.routeruser, self.routerpass)
			return	
		else:
			found = self.activemacs(self.routerip, self.routeruser, self.routerpass, self.routercmdline)
			if found is not None:
				someonehome=False
				for friendlyid, mac in self.monitormacs.items():
					if mac in found:
						someonehome=True
						self.updatestatus(self.devid2domid[friendlyid], True)
						if friendlyid in self.timelastseen:
							self.timelastseen.pop(friendlyid, None)
					else:
						if friendlyid in self.timelastseen:
							if not datetime.now() - self.timelastseen[friendlyid] > timedelta(seconds=self.graceoffline):
								Domoticz.Debug("Check if realy offline: " + str(friendlyid))
								someonehome=True
							else:
								Domoticz.Debug("Considered absent: " + str(friendlyid))
								self.updatestatus(self.devid2domid[friendlyid], False)
						else:
							self.timelastseen[friendlyid] = datetime.now()
							Domoticz.Debug("Seems to have went offline: " + str(friendlyid))
							someonehome=True
				self.updatestatus(1, someonehome)	 
			else:
				Domoticz.Error("No list of connected WLAN devices from router")
				
global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

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
		Domoticz.Debug("Device:			  " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:		 '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:	 '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:	  " + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:	 '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	return
