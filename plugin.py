# Domoticz Python Plugin to monitor router for presence/absence of wifi devices without pinging them (pinging can drain your phone battery).
#
# Author: ESCape
#
"""
<plugin key="idetect" name="iDetect Wifi presence detection " author="ESCape" version="0.6.1">
	<description>
		<h2>Presence detection by router</h2><br/>
		<h3>Authentication settings</h3>
		<ul style="list-style-type:square">
			<li>You can monitor multiple routers by separating their ip addresses with a comma. If you monitor more than one router the username (and optional password) must be the same on all of them.</li>
			<li>Leave the password field empty to use ssh public key authentication.</li>
			<li>SSH key authentication must be configured on every router and on the OS (linux) using ~/.ssh/id_rsa.pub for the user running domoticz.</li>
			<li>If you enter a password in the password field, then the plugin can use password authentication. Make sure you have installed sshpass (sudo apt-get install sshpass). This is much easier than key authentication, but less secure. Your password wil be stored in the Domoticz database in plain text.</li>
		</ul>
		<h3>Behaviour settings</h3>
		<ul style="list-style-type:square">
			<li>Enter mac addresses to monitor in the format phone1=F1:2A:33:44:55:66,phone2=B9:88:77:C6:55:44 (and more, separated by comma).
			The name should be short and descriptive. It  will be used as the identifying deviceID and the initial device name. You can change the devices name after it has been created.</li>
			<li>'remove obsolete' gives you a choice to automatically delete devices that are no longer in de above list of mac-addresses OR to show them as timedout.</li>
			<li>The grace period should be a multitude of the poll interval in seconds. It controls after how long phones are shown as absent (confirmation from several polls to deal with temporarily dropped connections). Example of a working but illogical configuration: if the grace period is 20 seconds, but the poll interval is 30 seconds it might still take up to a minute to confirm absence (2 poll cycles)</li>
			<li>The override button will let the 'Anyone home' device think there is someone home, even if no presence is detected. This can be helpfull for visitors or to take some control over the 'Anyone home' status from other scripts.</li>
			<li>The plugin will automatically determine which command to use on the router for which wireless interfaces. If your router (chipset) is not supported you can experiment how to get the right info from the router and post that info on the forum. I might be able to add support to the plugin.</li>
		</ul>
	</description>
	<params>
		<param field="Address" label="Wifi router IP Address" width="200px" required="true" default="192.168.0.1"/>
		<param field="Username" label="Username" width="200px" required="true" default=""/>
		<param field="Password" label="Password" width="200px" required="false" default="" password="true"/>
		<param field="Mode1" label="MAC addresses te monitor" width="500px" required="true" default="phone1=A1:B1:01:01:01:01,phone2=C2:D2:02:02:02:02"/>
		<param field="Mode6" label="Remove obsolete" width="250px">
			<options>
				<option label="Delete obsolete devices" value="True" default="true"/>
				<option label="Show obsolete devices as unavailable" value="False"/>
			</options>
		</param>
		<param field="Mode2" label="Poll every" width="75px" required="true" default="10">
			<options>
				<option label="10 seconds" value=10/>
				<option label="15 seconds" value=15 default="true"/>
				<option label="30 seconds" value=30/>
				<option label="60 seconds" value=60/>
				<option label="2 minutes" value=120/>
				<option label="5 minutes" value=300/>
				<option label="10 minutes" value=600/>
				<option label="30 minutes" value=1800/>
			</options>
		</param>
		<param field="Mode3" label="Grace period (sec)" width="75px" required="true" default="30"/>
		<param field="Mode4" label="Override button" width="250px">
			<options>
				<option label="Do not allow override" value="No" default="true"/>
				<option label="Override for 1 hour" value="1"/>
				<option label="Override for 4 hours" value="4"/>
				<option label="Override for 8 hours" value="8"/>
				<option label="Override for 24 hours" value="24"/>
				<option label="Override indefinately" value="Forever"/>
				<option label="Override until next real presence" value="Next"/>
			</options>
		</param>
		<param field="Mode5" label="Debug mode" width="250px">
			<options>
				<option label="Off" value="False" default="true"/>
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
		if self.errorcount == 5 and not self.slowdown:
			Domoticz.Error("Temporarily limiting the polling frequency after encountering 5 (ssh) errors in a row.")
			self.slowdown=True
			if int(Parameters["Mode2"]) < 120:
				self.setpollinterval(120, True)
		if passwd:
			Domoticz.Debug("Using password instead of ssh public key authentication (less secure!)")
			cmd =["sshpass", "-p", passwd, self.sshbin, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=" + str(sshtimeout), user+"@"+host, routerscript]
		else:
			Domoticz.Debug("Using ssh public key authentication (~/.ssh/id_rsa.pub) for OS user running domoticz.")
			cmd =[self.sshbin, "-o", "ConnectTimeout=" + str(sshtimeout), user+"@"+host, routerscript]
			if self.debug and self.errorcount != 0:
				try:
					osuser=subprocess.check_output("whoami", timeout=1)
					runasuser = osuser.decode("utf-8").strip()
					Domoticz.Log("The OS user profile running domoticz is:	" + str(runasuser))
				except subprocess.CalledProcessError as err:
					Domoticz.Error("Trying to determine OS user raised an error (error: " + str(err.returncode) + "):" + str(err.output))
		if self.debug:
			Domoticz.Log("Fetching data from router using: " + str(cmd))
		try:
			completed=subprocess.check_output(cmd, timeout=alltimeout)
			if self.debug:
				Domoticz.Log("ssh command (router) returned:" + str (completed))
			if completed == "":
				Domoticz.Error("Router returned empty response.")
				self.errorcount += 1
				return False, "<Empty reponse>"
		except subprocess.CalledProcessError as err:
			Domoticz.Error("SSH subprocess failed with error (" + str(err.returncode) + "):" + str(err.output))
			self.errorcount += 1
			return False, "<Subprocess failed>"
		if self.slowdown:
			Domoticz.Status("Connection restored. Resuming at set poll interval")
			self.setpollinterval(int(Parameters["Mode2"]))
			self.slowdown = False
		self.errorcount = 0
		return True, completed

	def routercommand(self, host, user, passwd, mode='preferhw'):
		#The routerscript below will run on the router itself to determine which command and interfaces to use
		#Preferred method is 'wl' command, but this plugin can use 'arp' as fallback
		#The constructed command should return a clean list of mac addresses. One address per line in the format xx:xx:xx:xx:xx:xx.
		#Mac addresses from all known wireless interfaces should be included. Case doesn't matter, we'll take care of that when using the data.
		routerscript="""#!/bin/sh
					export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
					hwmethod=false"""
		if mode == 'preferhw':
			routerscript=routerscript+"""
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
							hwmethod=true
					fi
					test=$(which iwinfo > /dev/null 2>&1)
					if [ $? == 0 ]; then
							if [ "$hwmethod" == true ]; then
								printf "#"
							fi
							printf "iwinfo@"
							for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep '^eth\|^wlan\|^ath')
							do
									test=$(iwinfo $iface assoclist > /dev/null 2>&1)
									if [ $? == 0 ]; then
											printf "$iface "
									fi
							done
							hwmethod=true
					fi
					test=$(which wlanconfig > /dev/null 2>&1)
					if [ $? == 0 ]; then
							if [ "$hwmethod" == true ]; then
								printf "#"
							fi
							printf "wlanconfig@"
							for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep '^eth\|^wlan\|^ath')
							do
									test=$(wlanconfig $iface list > /dev/null 2>&1)
									if [ $? == 0 ]; then
											printf "$iface "
									fi
							done
							hwmethod=true
					fi
					test=$(which qcsapi_sockrpc > /dev/null 2>&1)
                    if [ $? == 0 ]; then
							if [ "$hwmethod" == true ]; then
								printf "#"
							fi
                			printf "qcsapi_sockrpc@"
							for iface in $(qcsapi_sockrpc get_primary_interface)
							do
									test=$(qcsapi_sockrpc get_assoc_records $iface > /dev/null 2>&1)
                                	if [ $? == 0 ]; then
                                            printf "$iface "
                                    fi
                            done
                            hwmethod=true
                    fi

					if [ "$hwmethod" == true ] ; then
						exit
					fi"""

		if mode != 'preferarp':
			routerscript=routerscript+"""
					test=$(which brctl > /dev/null 2>&1)
					if [ $? == 0 ]; then
							printf "brctl"
							exit
					fi"""
		routerscript=routerscript+"""
					test=$(which arp > /dev/null 2>&1)
					if [ $? == 0 ]; then
							printf "arp"
							exit
					fi
					if [ -f /proc/net/arp ]; then
						printf "procarp"
						exit
					fi
					printf none"""

		Domoticz.Debug("Checking router capabilities and wireless interfaces of " + host)
		success, sshdata=self.getfromssh(host, user, passwd, routerscript, alltimeout=4, sshtimeout=2)
		if success:
			capabilities = sshdata.decode("utf-8").split("#")
			Domoticz.Debug("Capabilities data from router(" + host + "): " + str(capabilities))
			pollscript = ""
			for capability in capabilities:
				gotinfo = capability.split("@")
				method = gotinfo[0]
				interfaces = gotinfo[-1].split()
				Domoticz.Debug("Parsed data from router (" + host + "): " + str(gotinfo))
				if method=="wl":
					Domoticz.Status("Using chipset specific (wl) command on router " + host + " for interfaces " + str(interfaces))
					for knownif in interfaces:
						pollscript=pollscript + ";wl -i " + knownif + " assoclist | cut -d' ' -f2"
				elif method=="iwinfo":
					Domoticz.Status("Using chipset specific (iwinfo) command on router " + host + " for interfaces " + str(interfaces))
					for knownif in interfaces:
						pollscript=pollscript + ";iwinfo " + knownif + " assoclist | grep '^..:..:..:..:..:.. ' | cut -d' ' -f1"
				elif method=="wlanconfig":
					Domoticz.Status("Using chipset specific (wlanconfig) command on router " + host + " for interfaces " + str(interfaces))
					for knownif in interfaces:
						pollscript=pollscript + ";wlanconfig " + knownif + " list | grep '^..:..:..:..:..:.. ' | cut -d' ' -f1"
				elif method=="qcsapi_sockrpc":
					Domoticz.Status("Using chipset specific (qcsapi_sockrpc) command on router " + host + " for interfaces " + str(interfaces))
					for knownif in interfaces:
						pollscript=pollscript + ";concount=$(qcsapi_sockrpc get_count_assoc " + knownif + ");i=1;while [[ $i -le $concount ]]; do qcsapi_sockrpc get_station_mac_addr " + knownif + " $i;i=$((i+1));done"				
				elif method=="brctl":
					Domoticz.Status("Using generic (brctl) instead of chipset specific command on router " + host + " (slower response to absence)")
					pollscript += ";brctl showmacs br0 | grep '..:..:..:..:..:..' | awk '{print $ 2}'"
				elif method=="arp":
					Domoticz.Status("Using generic (arp) instead of chipset specific command on router " + host + " (slower and on some routers less reliable response to absence)")
					pollscript += ";arp -a | grep '..:..:..:..:..:..' | awk '{print $ 4}'"
				elif method=="procarp":
					Domoticz.Status("Using last resort method for router " + host + " (read info from /proc/net/arp file). This method has a slower and less reliable response to absence)")
					pollscript += ";cat /proc/net/arp | grep '..:..:..:..:..:..' | awk '{print $ 4}'"
				else:
					Domoticz.Error("Unable to construct router commandline for presence method " + method + "on router " + host)
			if pollscript != "":
				pollscript = "export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH" + pollscript
				pollscript += ";exit"
				Domoticz.Debug("Constructed this cmd for the router " + host + " to poll for present phones: " + pollscript)
				return pollscript
			else:
				Domoticz.Error("Could not determine router capabilities for " + host)
				return "none"
		else:
			Domoticz.Error("Could not retreive router capabilities from " + host)
			return "none"

	def activemacs(self, host, user, passwd, routerscript):
		Domoticz.Debug("Polling present phones from router")
		success, sshdata=self.getfromssh(host, user, passwd, routerscript)
		if success:
			list=[]
			for item in sshdata.splitlines():
				list.append(item.decode("utf-8").upper())
			return True, list
		else:
			Domoticz.Debug("Failed to poll present phones from router")
			return False, None

	def createdevice(self, name, unit, friendlyid, iconid):
		Domoticz.Log("creating device for " + friendlyid + " with unit id " + str(unit)) 
		Domoticz.Device(Name=name, Unit=unit, DeviceID=friendlyid, TypeName="Switch", Used=1, Image=iconid).Create()
		try:
			Devices[unit].Update(nValue=0, sValue="Off")
			Domoticz.Debug("Created new device named " + str(friendlyid) + " with unitid " + str(unit))
			success=True
		except Exception as err:
			Domoticz.Error("Error creating device for " + friendlyid + ". Make sure domoticz is accepting new devices/sensors (in domoticz settings). " + str(err))
			success=False
		return success

	def updatestatus(self, id, onstatus):
		if onstatus:
			svalue = "On"
			nvalue = 1
		else:
			svalue = "Off"
			nvalue = 0
		if id not in Devices:
			Domoticz.Log("Device " + str(id) + " does not exist. Restart the plugin to reinitialize devices.")
			return
		if Devices[id].nValue != nvalue or Devices[id].sValue != svalue:
			Devices[id].Update(nValue=nvalue, sValue=svalue)
			Domoticz.Debug("Changing device " + Devices[id].Name + " to " + svalue)

	def setpollinterval(self, target, delayrun=False):
		if target > 30:
			self.skipbeats=target/30
			if delayrun:
				self.beats=1
			else:
				self.beats=self.skipbeats
			Domoticz.Heartbeat(30)
		else:
			self.skipbeats=0
			self.beats=1
			Domoticz.Heartbeat(target)

	def onStart(self):
		#setup debugging if enabled in settings
		if Parameters["Mode5"]=="True":
			Domoticz.Debugging(1)
			self.debug=True
		else:
			self.debug=False

		self.initcomplete=False
		self.initfailures=False
		self.slowdown=False

		#Select or create icons for devices
		homeicon="idetect-home"
		uniticon="idetect-unithome"
		overrideicon="idetect-override"

		try:
			if homeicon not in Images: Domoticz.Image('ihome.zip').Create()
			homeiconid=Images[homeicon].ID
			if uniticon not in Images: Domoticz.Image('iunit.zip').Create()
			uniticonid=Images[uniticon].ID
			if overrideicon not in Images: Domoticz.Image('ioverride.zip').Create()
			overrideiconid=Images[overrideicon].ID
		except:
			Domoticz.Error("Could not find or use the required icon (.zip) files. Plugin installation seems incomplete. Aborting initialization.")
			return

		#check some (OS) requirements
		if onwindows():
			Domoticz.Debug('Running on Windows')
			self.sshbin = 'C:\Windows\SysNative\OpenSSH\ssh'
			Domoticz.Error('The plugin does not work on windows for reasons unknow. Hearbeat code is not executed. If you can offer any help fixing this please let me know on forumthread')
		else:
			Domoticz.Debug('Not running on Windows')
			self.sshbin = 'ssh'

		if not oscmdexists(self.sshbin + " -V"):
			Domoticz.Error("Aborting plugin initialization because SSH client failure (missing?)")
			return

		self.routeruser = Parameters["Username"]
		self.routerpass = Parameters["Password"]
		if self.routerpass != "":
			if not oscmdexists("sshpass -V"):
				Domoticz.Error("A SSH password is set for the plugin, but the sshpass command seems to be unavailable. Please install it first.")
				return

		#prepare variables and use the remaining parameters from te settings page
		self.monitormacs={}
		self.macmonitorcount=0
		devmacs=Parameters["Mode1"].replace(" ", "").split(",")
		for item in devmacs:
			try:
				devpart, option = item.split("#")
				if option.strip().lower() == "ignore":
					ignore = True
				else:
					ignore = False
			except:
				devpart = item
				ignore = False
			try:
				name, mac = devpart.split("=")
				self.monitormacs.update({name.strip():{'mac': mac.strip().upper(), 'ignore': ignore, 'lastseen':None}})
				if not ignore:
					self.macmonitorcount += 1
			except:
				Domoticz.Error("Invalid device/mac setting in: " + str(devmacs))
		Domoticz.Debug("Monitoring " + str(self.monitormacs) + " for presence.")
		Domoticz.Debug(str(self.macmonitorcount) + " of them will control the Anyone home switch")

		self.graceoffline = int(Parameters["Mode3"])

		#parse the address parameter for optional power options
		self.detectmode = 'preferhw'
		if len(Parameters["Address"].split("#")) > 1:
			for poweroption in Parameters["Address"].split("#")[1:]:
				if poweroption.lower().strip() == "forcegeneric":
					self.detectmode = 'anygeneric'
				if poweroption.lower().strip() == "forcearp":
					self.detectmode = 'preferarp'

		#parse one or multiple router ips from settings
		#Note: the poweroption, username and password are set globally for all routers!
		routerips = Parameters["Address"].split("#")[0].strip()
		self.routercmd = {}
		for router in routerips.split(','):
			thisrouter = router.strip()
			usecmd = self.routercommand(thisrouter, self.routeruser, self.routerpass, mode=self.detectmode)
			if usecmd != "none":
				self.routercmd[thisrouter] = usecmd

		Domoticz.Debug("Dictionary of routers and commands: " + str(self.routercmd))
		self.deleteobsolete = Parameters["Mode6"] == "True"
		self.devid2domid={}

		#Create "Anyone home" device
		if 1 not in Devices:
			if self.createdevice(name="Anyone", unit=1, friendlyid="#Anyone", iconid=homeiconid):
				Domoticz.Status("Device created for general/Anyone presence")
			else:
				self.initfailures=True

		#Create "Override" device
		if 255 not in Devices:
			if self.createdevice(name="Override", unit=255, friendlyid="#Override", iconid=overrideiconid):
				Domoticz.Status("Override switch created to override absence with presence")
			else:
				self.initfailures=True

		#Set the override options
		if Parameters["Mode4"] == "No":
			self.overrideallow=False
			self.overridefor=None
			self.overrideuntilnext=False
		elif Parameters["Mode4"] == "Next":
			self.overrideallow=True
			self.overridefor=None
			self.overrideuntilnext=True
		elif Parameters["Mode4"] == "Forever":
			self.overrideallow=True
			self.overridefor=None
			self.overrideuntilnext=False
		else:
			self.overrideallow=True
			self.overridefor=int(Parameters["Mode4"])
			self.overrideuntilnext=False
		#Get last update timestamp for temporary override in case Domoticz was restarted during the override time
		if self.overridefor and Devices[255].nValue==1:
			self.overridestart=timestampfromstring(Devices[255].LastUpdate)
			Domoticz.Debug("Override start time recovered after restart. Set to " + str(self.overridestart))

		#Find obsolete device units (no longer configured te be monitored)
		deletecandidates=[]
		for dev in Devices:
			if dev == 1:
				continue
			#Check if devices are still in use
			Domoticz.Debug("monitoring device: " + Devices[dev].Name)
			if Devices[dev].DeviceID in self.monitormacs: #prep for use
				Domoticz.Debug(Devices[dev].Name + " is stil in use")
				self.devid2domid.update({Devices[dev].DeviceID:dev})
			else: #delete device
				if dev != 1 and dev != 255:
					if self.deleteobsolete:
						Domoticz.Log("deleting device unit: " + str(dev) + " named: " + Devices[dev].Name)
						deletecandidates.append(dev)
					else:
						Devices[dev].Update(nValue=0, sValue="Off", TimedOut=1)

		Domoticz.Debug("devid2domid: " + str(self.devid2domid))
		Domoticz.Debug("monitormacs: " + str(self.monitormacs))

		for obsolete in deletecandidates:
			Devices[obsolete].Delete()

		#Check if there is a Domoticz device for every configured MAC address
		for friendlyid in self.monitormacs:
			if friendlyid not in self.devid2domid:
				Domoticz.Debug(friendlyid + " not in known device list")
				numavailable=False
				for num in range(2,200):
					if num not in Devices:
						numavailable=True
						if self.createdevice(name=friendlyid, unit=num, friendlyid=friendlyid, iconid=uniticonid):
							self.devid2domid.update({Devices[num].DeviceID:num})
						else:
							self.initfailures=True
						break
				if not numavailable:
					Domoticz.Error("No numbers left to create device for " + friendlyid)
					self.initfailures=True

		#Finalizing the initialization by setting the heartbeat needed for poll interval
		self.setpollinterval(int(Parameters["Mode2"]))
		if not self.initfailures:
			self.initcomplete=True
		Domoticz.Debug("Plugin initialization done.")

	def onHeartbeat(self):
		if not self.initcomplete:
			Domoticz.Error("Plugin initialization did not complete successfully. Check the (debug) log for startup errors.")
			return
		#Cancel the rest of this function if this heartbeat needs to be skipped
		if self.beats < self.skipbeats:
			Domoticz.Debug("Skipping heartbeat: " + str(self.beats))
			self.beats += 1
			return
		self.beats=1
		#Reset the override switch if set for a fixed duration that has expired 
		if Devices[255].nValue==1 and self.overridefor:
			if datetime.now() - self.overridestart > timedelta(hours=self.overridefor):
				self.updatestatus(255, False)
				self.overridestart=None
		#Start searching for present devices
		Domoticz.Debug("devid2domid: " + str(self.devid2domid))
		if len(self.routercmd) < 1:
 			#something must have gone wrong while initializing the plugin. 
 			Domoticz.Error("No usable commandlines or routers to check presence. Check configuration and routers.")
 			return
		else:
			found = []
			success = False
			for router in self.routercmd:
				ok, thisrouterdata = self.activemacs(router, self.routeruser, self.routerpass, self.routercmd[router])
				if ok:
					found += thisrouterdata
				success = success or ok
			if success:
				Domoticz.Debug("Found these devices connected:" + str(found))
				homecount=0
				gonecount=0
				for friendlyid in self.monitormacs:
					if self.monitormacs[friendlyid]['mac'] in found:
						if not self.monitormacs[friendlyid]['ignore']:
							homecount += 1
						self.updatestatus(self.devid2domid[friendlyid], True)
						if self.monitormacs[friendlyid]['lastseen']:
							self.monitormacs[friendlyid]['lastseen'] = None
					else:
						if self.monitormacs[friendlyid]['lastseen']:
							if not datetime.now() - self.monitormacs[friendlyid]['lastseen'] > timedelta(seconds=self.graceoffline):
								Domoticz.Debug("Check if realy offline: " + str(friendlyid))
							else:
								Domoticz.Debug("Considered absent: " + str(friendlyid))
								self.updatestatus(self.devid2domid[friendlyid], False)
								if not self.monitormacs[friendlyid]['ignore']:
									gonecount += 1
						else:
							self.monitormacs[friendlyid]['lastseen'] = datetime.now()
							Domoticz.Debug("Seems to have went offline: " + str(friendlyid))

				if self.debug:
					if (homecount + gonecount) != self.macmonitorcount:
						Domoticz.Status("Homecount=" + str(homecount) + "; Gonecount=" + str(gonecount) + "; Totalmacs=" + str(self.macmonitorcount))
						Domoticz.Status("Awaiting confirmation on absence of " + str(self.macmonitorcount-(homecount+gonecount)) + " devices")
				#Set Anyone home device based on MAC detection and Override status
				if homecount > 0:
					self.updatestatus(1, True)
					if self.overrideuntilnext:
						self.updatestatus(255, False)
				elif Devices[255].nValue==1:
					self.updatestatus(1, True)
				elif gonecount == self.macmonitorcount:
					self.updatestatus(1, False)
			else:
				Domoticz.Error("No list of connected WLAN devices from router")

	def onCommand(self, Unit, Command, Level, Hue):
		#only allow the override switch to be operated and only if overrides are enabled
		if Unit == 255:
			if str(Command)=='On' and self.overrideallow:
				self.updatestatus(Unit, True)
				self.updatestatus(1, True)
				if self.overridefor:
					self.overridestart=datetime.now()
			if str(Command)=='Off':
				self.updatestatus(Unit, False)
				self.overridestart=None
		return

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

# Generic helper functions
def oscmdexists(cmd):
	try:
		result = subprocess.check_output(cmd, timeout=1, shell=True)
	except subprocess.CalledProcessError as err:
		Domoticz.Error("trying [" + cmd + "] raised an error (error: " + str(err.returncode) + "):" + str(err.output))
		return False
	Domoticz.Debug("Checking if [" + cmd + "] will run: OK")
	return True

#Check if the plugin (and Domoticz) is running on Windows
def onwindows():
	if str(Parameters['HomeFolder'])[1:3] == ":\\":
		return True
	else:
		return False

#Workaround for the buggy datetime.strptime()
#strptime will only work once and then trow exceptions (seems to be known bug)
def timestampfromstring(input):
	#format is "%Y-%m-%d %H:%M:%S"
	if len(input) == 19:
		try:
			thistimestamp=datetime(int(input[:4]),int(input[5:7]),int(input[8:10]),int(input[11:13]),int(input[14:16]),int(input[17:19]))
			return thistimestamp
		except:
			Domoticz.Error("Could not parse datetime string " + input + ". Returning the current instead of time of last update.")
	return datetime.now()

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
