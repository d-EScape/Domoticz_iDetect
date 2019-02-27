# Domoticz Python Plugin to monitor router for presence/absence of wifi devices without pinging them (pinging can drain your phone battery).
#
# Author: ESCape
#
"""
<plugin key="idetect" name="iDetect Wifi presence detection " author="ESCape" version="0.7.7">
	<description>
		<h2>Presence detection by router</h2><br/>
		<h3>Authentication settings</h3>
		<ul style="list-style-type:square">
			<li>You can monitor multiple routers by separating their ip addresses with a comma. If you monitor more than one router the username for all of them will default to the value entered in password field, or you can specify a router specific username by naming the router username@routerip (eg admin@192.168.1.1)</li>
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
import re
import subprocess

class BasePlugin:

	def __init__(self):
		self.monitormacs = {}
		self.graceoffline = 0
		self.timelastseen = {}
		self.mac_format = re.compile(r'[a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}')
		return

	def getfromssh(self, host, user, passwd, routerscript, port=22, alltimeout=5, sshtimeout=3):
		if passwd:
			Domoticz.Log("Using password instead of ssh public key authentication for " + host + " (less secure!)")
			cmd =["sshpass", "-p", passwd, self.sshbin, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(port), user+"@"+host, routerscript]
			Domoticz.Debug("Fetching data from " + host + " using: " + " ".join(cmd[:2]) + " **secret** " + " ".join(cmd[3:]))
		else:
			if self.keyfile != '':
				cmd =[self.sshbin, "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(port), user+"@"+host, routerscript]
			else:
				cmd =[self.sshbin, "-i", self.keyfile, "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(port), user+"@"+host, routerscript]
			Domoticz.Debug("Fetching data from " + host + " using: " + " ".join(cmd))
		starttime=datetime.now()
		success = True
		try:
			output=subprocess.check_output(cmd, timeout=alltimeout)
			Domoticz.Debug("ssh command on " + host + " returned:" + str (output))
		except subprocess.CalledProcessError as err:
			Domoticz.Debug("SSH subprocess for " + host + " failed with error (" + str(err.returncode) + "):" + str(err.output))
			success = False
			output = "<Subprocess failed>"
		except subprocess.TimeoutExpired:
			Domoticz.Debug("SSH subprocess for " + host + " timeout")
			success = False
			output = "<Timeout>"
		except Exception as err:
			Domoticz.Debug("Subprocess for " + host + " failed with error: " + err)
			success = False
			output = "<Unknown error>"
		else:
			if output == "":
				Domoticz.Error("Router " + host + " returned empty response.")
				success = False
				output = "<Empty reponse>"
		timespend=datetime.now()-starttime
		Domoticz.Debug("SSH command on " + host + " took " + str(timespend.microseconds//1000) + " milliseconds.")
		return success, output

	def getrouter(self, host, user, passwd, routerport=22, mode='preferhw', prefabcmd=''):
		#The routerscript(s) below will run on the router itself to determine which command and interfaces to use
		#The constructed command should return a clean list of mac addresses. One address per line in the format xx:xx:xx:xx:xx:xx.
	
		#lists of router methods/chipsets supported by the plugin
		#wl = broadcom
		#iwinfo = mac80211
		#wlanconfig = atheros
		#qcsapi_sockrpc = quantenna 
		hwmethods=['wl', 'iwinfo', 'wlanconfig', 'qcsapi_sockrpc']
		swmethods=['brctl','arp','procarp']

		#gets all available commands from a router
		methodq="""
#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
type wl > /dev/null 2>&1 && printf "~wl"
type iwinfo > /dev/null 2>&1 && printf "~iwinfo"
type wlanconfig > /dev/null 2>&1 && printf "~wlanconfig"
type qcsapi_sockrpc > /dev/null 2>&1 && printf "~qcsapi_sockrpc"
type brctl > /dev/null 2>&1 && printf "~brctl"
type arp > /dev/null 2>&1 && printf "~arp"
[ -f /proc/net/arp ] && printf "~procarp"
exit
"""
		#find interfaces suitable for a command (chipset)
		ifq={}
		ifq['wl']="""
#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan');do
	wl -i $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
exit
"""
		ifq['iwinfo']="""
#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath');do
	iwinfo $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
exit
"""

		ifq['wlanconfig']="""
#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath');do
	wlanconfig $iface list > /dev/null 2>&1 && printf "~$iface"
done
exit
"""

		ifq['qcsapi_sockrpc']="""
#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
for iface in $(qcsapi_sockrpc get_primary_interface);do
	qcsapi_sockrpc get_assoc_records $iface > /dev/null 2>&1 && printf "~$iface"
done
exit
"""

		generic={}
		generic['brctl']=";brctl showmacs br0 | grep '..:..:..:..:..:..' | awk '{print $ 2}'"
		generic['arp']=";arp -a | grep '..:..:..:..:..:..' | awk '{print $ 4}'"
		generic['procarp']=";cat /proc/net/arp | grep '..:..:..:..:..:..' | awk '{print $ 4}'"
		
		custom={}
		custom['routeros']="interface wireless registration-table print"
		custom['routeros-arp']="ip arp print"
		custom['zyxel-arp']="show arp-table"
		custom['unifiusg-arp']="show arp"
		custom['test']="arp -a"

		pollscript = ""

		#the forcegeneric option is replaced by the prefabcmd, but lets keep if for a little while for backwards compatibility 
		#TO BE REMOVED!!!!
		if mode=="anygeneric":
			prefabcmd="brctl"
		if mode=="preferarp":
			prefabcmd="arp"
		
		foundif = {}
		#Use preconfigured command/interface combo if available (instead of auto detection)
		if prefabcmd != "":
			Domoticz.Debug("Prefab command for " + host + "= >" + prefabcmd)
			#if a custom command is preconfigured just return that command without any additions and assume the output will not be formatted
			if prefabcmd in custom:
				pollscript=custom[prefabcmd]
				Domoticz.Log("Using preconfigured custom command on router " + host + ": " + pollscript)
				return True, {'user': user,'port': routerport, 'cmd': pollscript, 'initialized': True, 'prospone': datetime.now(), 'errorcount': 0}
			foundmethods=hwmethods + swmethods #assume every cmd is available
			sources=prefabcmd.strip().split('&')
			for source in sources:
				parts=source.strip().split()
				method=parts[0].strip()
				if len(parts) > 1:
					interfaces=parts[1:]
					foundif[method]=interfaces
				else:
					foundif[method]=[]
			Domoticz.Debug("Forcing command and interfaces for router " + host + ":" + str(foundif))
		else:
			#automatic detection
			#find all available commands (hw specific and generic) on router
			success, sshdata=self.getfromssh(host, user, passwd, methodq, port=routerport)
			if success:
				foundmethods = sshdata.decode("utf-8")[1:].split("~")
				Domoticz.Debug("Available commands on " + host + ":" + str(foundmethods))
			else:
				Domoticz.Debug("Could not retreive available commands on " + host)
				return False, {'user': user, 'port': routerport, 'cmd': '', 'initialized': False, 'prospone': datetime.now() + timedelta(seconds=12), 'errorcount': 1}

			#find the wifi interfaces for hw specific commands
			for method in hwmethods:
				if method in foundmethods:
					success, sshdata=self.getfromssh(host, user, passwd, ifq[method], port=routerport)
					if success:
						interfaces = sshdata.decode("utf-8")[1:].split("~")
						foundif[method]=interfaces
					else:
						Domoticz.Debug("Could not retreive interfaces belonging to " + method + " command on " + host)
			#need a generic command if nog suitable hw command was found (just 1!)
			if len(foundif) < 1:
				for method in swmethods:
					if method in foundmethods:
						foundif[method]=[]
						break
			Domoticz.Debug("Found suitable command (and interfaces) for router " + host + ":" + str(foundif))

		#construct the hw specific query commands
		for method in foundif:
			if len(foundif[method]) < 1 and method in hwmethods:
				Domoticz.Error("Got no interfaces for " + method + " command on " + host)
				continue
			if method=="wl":
				for knownif in foundif[method]:
					pollscript=pollscript + ";wl -i " + knownif + " assoclist | cut -d' ' -f2"
			elif method=="iwinfo":
				for knownif in foundif[method]:
					pollscript=pollscript + ";iwinfo " + knownif + " assoclist | grep '^..:..:..:..:..:.. ' | cut -d' ' -f1"
			elif method=="wlanconfig":
				for knownif in foundif[method]:
					pollscript=pollscript + ";wlanconfig " + knownif + " list | grep '^..:..:..:..:..:.. ' | cut -d' ' -f1"
			elif method=="qcsapi_sockrpc":
				for knownif in foundif[method]:
					pollscript=pollscript + ";concount=$(qcsapi_sockrpc get_count_assoc " + knownif + ");i=0;while [[ $i -lt $concount ]]; do qcsapi_sockrpc get_station_mac_addr " + knownif + " $i;i=$((i+1));done"				
			elif method in swmethods:
				if pollscript == "":
					pollscript = generic[method]
					Domoticz.Log("Using generic " + method + " command on router " + host + ". Will respond slower and on some routers a little less reliable to absence")
					break
			else:
				Domoticz.Error("Unsupported command (pre)configured for " + host + ": " + method)
			if method in hwmethods:
				Domoticz.Log("Using chipset specific " + method + " command on router " + host + " for interfaces " + " & ".join(foundif[method]) + " (=" + method + " " + " ".join(foundif[method]) + ")")

		if pollscript == "":
			Domoticz.Debug("Could not construct router query command for " + host)
			return False, {'user': user,'port': routerport, 'cmd': '', 'initialized': False, 'prospone': datetime.now() + timedelta(seconds=12), 'errorcount': 1}
		else:
			pollscript = "export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH" + pollscript + ";exit"
			Domoticz.Debug("Constructed this cmd for the router " + host + " to poll for present phones: " + pollscript)
			return True, {'user': user,'port': routerport, 'cmd': pollscript, 'initialized': True, 'prospone': datetime.now(), 'errorcount': 0}

	def getactivemacs(self, router):
		errorcount=self.routers[router]['errorcount']
		if self.routers[router]['initialized']:
			Domoticz.Debug("Polling presense data from " + router)
			success, sshdata=self.getfromssh(router, self.routers[router]['user'], self.routerpass, self.routers[router]['cmd'], port=self.routers[router]['port'])
			if success:
				if errorcount > 0:
					self.routers[router]['errorcount'] = 0
					Domoticz.Log('Connection restored for ' + router)

				list = self.mac_format.findall(sshdata.decode("utf-8").upper())
				return True, list
		else:
			Domoticz.Debug(router + " was not properly initialized. Retrying to get router capabilities (and skipping this poll round).")
			gotit, self.routers[router] = self.getrouter(router, self.routers[router]['user'], self.routerpass, routerport=self.routers[router]['port'], mode=self.detectmode)
			if gotit:
				self.routers[router]['errorcount'] = 0
				return False, None
		#If anything worked we should have retuned by now
		self.routers[router]['errorcount'] = errorcount + 1
		delayme = min(120, self.routers[router]['errorcount'] * 30)
		self.routers[router]['prospone'] = datetime.now() + timedelta(seconds=delayme)
		if self.routers[router]['errorcount'] % 3 == 0:
			if self.routers[router]['initialized']:
				Domoticz.Error('Polling ' + router + ' has failed ' + str(self.routers[router]['errorcount']) + ' times. Poll interval automatically reduced for this router.')
			else:
				Domoticz.Error('Failed ' + str(self.routers[router]['errorcount']) + ' times to get capabilities for ' + router + '. Retry interval automatically reduced for this router.')
		Domoticz.Debug('Routerinfo:' + str(self.routers[router]))
		return False, None

	def createdevice(self, name, unit, friendlyid, iconid):
		Domoticz.Log("creating device for " + friendlyid + " with unit id " + str(unit))
		Domoticz.Device(Name=name, Unit=unit, DeviceID=friendlyid, TypeName="Switch", Used=1, Image=iconid).Create()
		try:
			Devices[unit].Update(nValue=0, sValue="Off")
		except Exception as err:
			Domoticz.Error("Error creating device for " + friendlyid + ". Make sure domoticz is accepting new devices/sensors (in domoticz settings). " + str(err))
			success=False
		else:
			Domoticz.Log("Created new device named " + str(friendlyid) + " with unitid " + str(unit))
			success=True
		return success

	def updatestatus(self, id, onstatus):
		if onstatus:
			svalue = "On"
			nvalue = 1
		else:
			svalue = "Off"
			nvalue = 0
		if id not in Devices:
			Domoticz.Error("Device " + str(id) + " does not exist. Restart the plugin to reinitialize devices.")
			return
		if Devices[id].nValue != nvalue or Devices[id].sValue != svalue:
			Devices[id].Update(nValue=nvalue, sValue=svalue)
			Domoticz.Log("Changing presence of " + Devices[id].Name + " to " + svalue)

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
			Domoticz.Debugging(2)
			self.debug=True
		else:
			self.debug=False

		self.initcomplete=False
		self.initfailures=False
		self.slowdown=False
		self.pollfinished=True
		self.pollstart=None
		self.pollinterval=int(Parameters["Mode2"])

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

		if self.debug:
			try:
				osuser=subprocess.check_output("whoami", timeout=1)
				runasuser = osuser.decode("utf-8").strip()
				Domoticz.Log("The OS user profile running domoticz is:	" + str(runasuser))
			except subprocess.CalledProcessError as err:
				Domoticz.Debug("Trying to determine OS user raised an error (error: " + str(err.returncode) + "):" + str(err.output))

		if not oscmdexists(self.sshbin + " -V"):
			Domoticz.Error("Aborting plugin initialization because SSH client could not be found")
			return

		#get router user name and optional keyfile location for authentication
		Domoticz.Debug('Parsing user and optional keyfile from:' + str(Parameters["Username"]))
		try:
			self.routeruser, self.keyfile = Parameters["Username"].split("#")
		except:
			self.routeruser = Parameters["Username"]
			self.keyfile = ''
		else:
			Domoticz.Log('Using custom keyfile for authentication:' + self.keyfile)
		
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
					#Domoticz.Error("The #forcegeneric option has been replaced!! See instructions on GitHub")
					self.detectmode = 'anygeneric'
				if poweroption.lower().strip() == "forcearp":
					#Domoticz.Error("The #forcearp option has been replaced!! See instructions on GitHub")
					self.detectmode = 'preferarp'

		#parse one or multiple router ips from settings
		#Note: the poweroption, username and password are set globally for all routers!
		Domoticz.Debug('Router configuration:' + str(Parameters["Address"]))
		routerips = Parameters["Address"].split("#")[0].strip()
		self.routers={}
		for router in routerips.split(','):
			thisrouter = router.strip()
			try:
				username, hoststr = thisrouter.split("@")
			except:
				username = self.routeruser
				hoststr = thisrouter
			try:
				host, forcecmd = hoststr.split("=")
				hostcfg = None
			except:
				host = hoststr
				forcecmd = ""
				hostcfg = self.detectmode
			try:
				hostip, portstr = host.split(":")
				hostport = int(portstr)
			except:
				hostip = host
				hostport = 22
			success, self.routers[hostip] = self.getrouter(hostip, username, self.routerpass, routerport=hostport, mode=hostcfg, prefabcmd=forcecmd)
		Domoticz.Debug('Router initialized as:' + str(self.routers))

		self.deleteobsolete = Parameters["Mode6"] == "True"
		self.devid2domid={}

		#Create "Anyone home" device
		if 1 not in Devices:
			if self.createdevice(name="Anyone", unit=1, friendlyid="#Anyone", iconid=homeiconid):
				Domoticz.Log("Device created for general/Anyone presence")
			else:
				self.initfailures=True

		#Create "Override" device
		if 255 not in Devices:
			if self.createdevice(name="Override", unit=255, friendlyid="#Override", iconid=overrideiconid):
				Domoticz.Log("Override switch created to override absence with presence")
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
			if Devices[dev].DeviceID in self.monitormacs: #prep for use
				Domoticz.Debug(Devices[dev].Name + " is stil in use")
				self.devid2domid.update({Devices[dev].DeviceID:dev})
			else: #delete device
				if dev != 1 and dev != 255:
					if self.deleteobsolete:
						Domoticz.Log("Removing device unit: " + str(dev) + " named: " + Devices[dev].Name)
						deletecandidates.append(dev)
					else:
						Domoticz.Log("Device unit: " + str(dev) + " named: " + Devices[dev].Name + " will no longer be monitored.")
						Devices[dev].Update(nValue=0, sValue="Off", TimedOut=1)

		Domoticz.Debug("Devicenames and their Domoticz (subdevice) index: " + str(self.devid2domid))
		Domoticz.Debug("MAC addresses to monitor: " + str(self.monitormacs))

		for obsolete in deletecandidates:
			Devices[obsolete].Delete()

		#Check if there is a Domoticz device for every configured MAC address
		for friendlyid in self.monitormacs:
			if friendlyid not in self.devid2domid:
				Domoticz.Debug(friendlyid + " not in known device list... going to create it.")
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
		self.setpollinterval(self.pollinterval)
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
		#Start searching for present devices on all configured routers
		if len(self.routers) < 1:
			Domoticz.Error("There are no routers to monitor. Please check your configuration.")
			return
		else:
			if not self.pollfinished:
				Domoticz.Log("Warning! Skipping this poll cycle because the previous session has not finished yet (investigate what is slowing things down if you frequently get this message).")
				return
			self.pollfinished=False
			self.pollstart=datetime.now()
			found = []
			success = False
			for router in self.routers:
				if datetime.now() < self.routers[router]['prospone']:
					Domoticz.Debug('Prosponed connection to ' + router + ' for ' + str(self.routers[router]['prospone']-datetime.now()))
				else:
					ok, thisrouterdata = self.getactivemacs(router)
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

				if (homecount + gonecount) != self.macmonitorcount:
					Domoticz.Debug("Homecount=" + str(homecount) + "; Gonecount=" + str(gonecount) + "; Totalmacs=" + str(self.macmonitorcount))
					Domoticz.Log("Awaiting confirmation on absence of " + str(self.macmonitorcount-(homecount+gonecount)) + " devices")
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
				Domoticz.Debug("Did not retreive WLAN information from any router")
			self.pollfinished=True
			timespend=(datetime.now()-self.pollstart).microseconds//1000
			pollload=100*timespend//(self.pollinterval*1000)
			if pollload > 50:
				Domoticz.Log("Warning! Entire poll took " + str(pollload) + "% of the poll interval time (" + str(timespend) + " milliseconds). Investigate what is slowing things down if you frequently get this message.")
			else:
				Domoticz.Debug("Entire poll took " + str(pollload) + "% of the poll interval time (" + str(timespend) + " milliseconds)")

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
		Domoticz.Debug("trying [" + cmd + "] raised an error (error: " + str(err.returncode) + "):" + str(err.output))
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
