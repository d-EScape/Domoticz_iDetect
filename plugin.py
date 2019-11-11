# Domoticz Python Plugin to monitor tracker for presence/absence of wifi devices without pinging them (pinging can drain your phone battery).
#
# Author: ESCape
#
"""
<plugin key="idetect" name="iDetect Wifi presence detection" author="ESCape" version="2.0">
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
		<param field="Address" label="Tracker/router Address" width="200px" required="true" default="192.168.0.1"/>
		<param field="Username" label="Username" width="200px" required="true" default=""/>
		<param field="Password" label="Password" width="200px" required="false" default="" password="true"/>
		<param field="Mode1" label="Tags to monitor (mac or ip)" width="500px" required="true" default="phone1=A1:B1:01:01:01:01,phone2=C2:D2:02:02:02:02"/>
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
import threading
from trackers import poll_methods
import helpers.data_helper as data_helper
from override_switch import override_switch

class tag_device():
	#domoticz id is de friendly name
	def __init__(self, tag_id, friendly_name, ignore_for_anyonehome=False, grace_period=0):
		self.tag_id = tag_id
		self.friendly_name = friendly_name
		self.ignore_for_anyonehome = ignore_for_anyonehome
		self.grace_period = grace_period
		self.present = False
		self.domoticz_unit = None
		self.is_obsolete = False
		self.went_offline_callback = None
		self.last_seen = datetime.now()
		self.domoticz_unit = get_or_create_unit(self.friendly_name)
		Domoticz.Debug('start get or create wireless device')
		self.present = get_domoticz_status(self.domoticz_unit)
		Domoticz.Debug(self.friendly_name + ' monitor tag_id:' + self.tag_id + ', domoticz unit:' + str(self.domoticz_unit))
		
	def i_see_you(self):
		self.last_seen = datetime.now()
		if not self.present:
			updated = update_domoticz_status(self.domoticz_unit, True)
			if updated:
				self.present = True
				Domoticz.Debug(self.friendly_name + ' was just seen --> set as present.')
		
	def check_if_seen(self):
		seconds_ago = data_helper.time_since_last(self.last_seen)
		if (seconds_ago > self.grace_period) and self.present:
			updated = update_domoticz_status(self.domoticz_unit, False)
			if updated:
				self.present = False
				Domoticz.Debug(self.friendly_name + ' has not been seen for ' + str(seconds_ago) + 'seconds --> set as absent.')


def find_available_unit():
	for num in range(2,200):
		if num not in Devices:
			return num
	return None

def get_or_create_unit(friendly_name, unit=None, icon='idetect-unithome'):
	for d in Devices:
		if Devices[d].DeviceID == friendly_name:
			return d
	#this only runs when doesn't exist
	#Select or create icons for devices
	icon_file = {}
	icon_file['idetect-home'] = "ihome.zip"
	icon_file['idetect-unithome'] = "iunit.zip"
	icon_file['idetect-override'] = "ioverride.zip"
	if not icon in icon_file:
		Domoticz.Error("Unknown icon requested for " + friendly_name + ": " + icon)
	try:
		Domoticz.Status(str(Images))
		if icon not in Images:
			Domoticz.Debug("Getting icon requested for " + friendly_name + ": " + icon + " from file:" + icon_file[icon])
			newimage = Domoticz.Image(Filename=icon_file[icon])
			newimage.Create()
			Domoticz.Debug("New image: " + str(newimage))
			Domoticz.Debug("Icon pepared... now use it")
		for i in Images:
			Domoticz.Debug("Existing image id:" + i + " : " + str(Images[i]))
		Domoticz.Debug("icon name: " + str(icon))
		if icon in Images:
			icon_id=Images[icon].ID
			Domoticz.Debug("Real icon_id to use: " + str(icon_id))
		else:
			icon_id=None
	except:
		Domoticz.Error("Could not find or use the required icon file (" + icon_file[icon] + ") for " + icon + ". Plugin installation seems incomplete.")
		icon_id = None
	if unit is None:
		new_unit = find_available_unit()
		if new_unit is None:
			Domoticz.Error('Could not find available Domticz UnitID to create ' + friendly_name)
			return None
	else:
		new_unit = unit
	try:
		Domoticz.Device(Name=friendly_name, Unit=new_unit, DeviceID=friendly_name, TypeName="Switch", Used=1, Image=icon_id).Create()
		Domoticz.Log("Created device for " + friendly_name + " with unit id " + str(new_unit))
	except:
		Domoticz.Log("FAILED to create device for " + friendly_name + " with unit id " + str(new_unit))
		new_unit = None
	return new_unit
	
def handle_unused_unit(unit, remove_it=False):
	if remove_it:
		Devices[unit].Delete()
	else:
		Devices[unit].Update(nValue=0, sValue='Off', TimedOut=1)
		
def get_domoticz_status(unit):
	if Devices[unit].nValue == True:
		return True
	else:
		return False
		
def update_domoticz_status(unit, status):
	if status:
		svalue = "On"
		nvalue = 1
	else:
		svalue = "Off"
		nvalue = 0
	if unit not in Devices:
		Domoticz.Error("Device unit " + str(unit) + " does not exist in Domoticz. Restart the plugin to reinitialize devices.")
		return False
	if Devices[unit].nValue != nvalue or Devices[unit].sValue != svalue:
		Devices[unit].Update(nValue=nvalue, sValue=svalue)
		Domoticz.Debug("Changed state of " + Devices[unit].Name + " to " + svalue)
	return True


class BasePlugin:

	def __init__(self):
		return

	def onStart(self):
		#setup debugging if enabled in settings
		if Parameters["Mode5"]=="True":
			Domoticz.Debugging(2)
			self.debug=True
		else:
			self.debug=False
			
		self.active_trackers={}
		self.tags_to_monitor={}

		self.present_count = 0
		self.anyone_home = False
		self.pollinterval=int(Parameters["Mode2"])
		
		self.ANYONE_HOME_UNIT = 1
		self.OVERRIDE_UNIT = 255

		#check some (OS) requirements
		if onwindows():
			Domoticz.Debug('Running on Windows')
			Domoticz.Error('The plugin does not work on windows for reasons unknow. Hearbeat code is not executed. If you can offer any help fixing this please let me know on forumthread')
		else:
			Domoticz.Debug('Not running on Windows')

		if self.debug:
			try:
				osuser=subprocess.check_output("whoami", timeout=1)
				runasuser = osuser.decode("utf-8").strip()
				Domoticz.Log("The OS user profile running domoticz is:	" + str(runasuser))
			except subprocess.CalledProcessError as err:
				Domoticz.Debug("Trying to determine OS user raised an error (error: " + str(err.returncode) + "):" + str(err.output))

		#get tracker user name and optional keyfile location for authentication
		Domoticz.Debug('Parsing user and optional keyfile from:' + str(Parameters["Username"]))
		try:
			self.trackeruser, self.keyfile = Parameters["Username"].split("#")
		except:
			self.trackeruser = Parameters["Username"]
			self.keyfile = ''
		else:
			Domoticz.Status('Using custom keyfile for authentication:' + self.keyfile)
		
		self.trackerpass = Parameters["Password"]
		if self.trackerpass != "":
			if not oscmdexists("sshpass -V"):
				Domoticz.Error("A SSH password is set for the plugin, but the sshpass command seems to be unavailable. Please install it first.")
				return
				
		#Create "Anyone home" device
		if self.ANYONE_HOME_UNIT not in Devices:
			get_or_create_unit('Anyone', unit=self.ANYONE_HOME_UNIT, icon='idetect-home')

		#Create "Override" device
		if self.OVERRIDE_UNIT not in Devices:
			get_or_create_unit('Override', unit=self.OVERRIDE_UNIT, icon='idetect-override')
				
		self.override = override_switch(Parameters["Mode4"])
		if get_domoticz_status(self.OVERRIDE_UNIT):
			update_domoticz_status(self.OVERRIDE_UNIT, self.override.set_active())

		#prepare variables and use the remaining parameters from te settings page
		self.graceoffline = int(Parameters["Mode3"])
		configured_tag_ids=Parameters["Mode1"].replace(" ", "").split(",")
		units_in_use=[]
		for item in configured_tag_ids:
			try:
				devpart, option = item.split("#")
				if option.strip().lower() == "ignore":
					ignore_me = True
				else:
					ignore_me = False
			except:
				devpart = item
				ignore_me = False
			try:
				friendly_name, tag_id = devpart.split("=")
				clean_name = friendly_name.strip()
				clean_tag_id = tag_id.strip().upper()
			except:
				Domoticz.Error("Invalid device/tag_id setting in: " + str(configured_tag_ids))
			self.tags_to_monitor[clean_tag_id]=tag_device(clean_tag_id, clean_name, ignore_me, self.graceoffline)
			if data_helper.is_ip_address(clean_tag_id):
				Domoticz.Debug('Will use local ping to monitor presence for: ' + clean_tag_id)
				if not 'local pinger' in self.active_trackers:
					self.active_trackers['local pinger']=poll_methods['ping']('local pinger', '0', 'irrelevant', 'irrelevant', 'irrelevant', 30)
					self.active_trackers['local pinger'].register_list_interpreter(self.onDataReceive)
				self.active_trackers['local pinger'].register_tag(clean_tag_id)
			units_in_use.append(self.tags_to_monitor[clean_tag_id].domoticz_unit)
			
		Domoticz.Debug("Monitoring " + str(self.tags_to_monitor) + " for presence.")
		self.deleteobsolete = Parameters["Mode6"] == "True"
		for d in Devices:
			if not d in units_in_use:
				if not d in [self.ANYONE_HOME_UNIT, self.OVERRIDE_UNIT]:
					handle_unused_unit(d, self.deleteobsolete)
		

		#parse one or multiple tracker ips from settings
		#Note: the poweroption, username and password are set globally for all trackers!
		Domoticz.Debug('Tracker configuration:' + str(Parameters["Address"]))
		trackerips = Parameters["Address"].split("#")[0].strip()
		for tracker in trackerips.split(','):
			thistracker = tracker.strip()
			try:
				host_user, host_config = thistracker.split("@")
			except:
				host_user = self.trackeruser
				host_config = thistracker
			try:
				host_address, host_type = host_config.split("=")
			except:
				host_address = host_config
				host_type = 'default' #default type
			try:
				host_ip, host_port_str = host_address.split(":")
				host_port = int(host_port_str)
			except:
				host_ip = host_address
				host_port = 22				
			self.active_trackers[host_ip]=poll_methods[host_type](host_ip, host_port, host_user, self.trackerpass, self.keyfile, self.pollinterval)
			self.active_trackers[host_ip].register_list_interpreter(self.onDataReceive)
		Domoticz.Debug('Trackers initialized as:' + str(self.active_trackers))
			
		Domoticz.Debug("Plugin initialization done.")
		Domoticz.Heartbeat(4)
			
	def onDataReceive(self, source):
		Domoticz.Debug('Inbound data from: ' + str(source.tracker_ip) + ' containing ' + str(source.found_tag_ids))
		for seen in source.found_tag_ids:
			if seen in self.tags_to_monitor:
				self.tags_to_monitor[seen].i_see_you()
		self.present_count = 0
		for d in self.tags_to_monitor:
			self.tags_to_monitor[d].check_if_seen()
		for d in self.tags_to_monitor:
			if self.tags_to_monitor[d].present and not self.tags_to_monitor[d].ignore_for_anyonehome:
				self.present_count = self.present_count + 1
		Domoticz.Debug(str(self.present_count) + ' devices are present (excluding ignored devices)')
		if (self.present_count == 0 and not self.override.active) and self.anyone_home:
			updated = update_domoticz_status(self.ANYONE_HOME_UNIT, False)
			if updated:
				self.anyone_home = False
		elif (self.present_count > 0 or self.override.active) and not self.anyone_home:
			updated = update_domoticz_status(self.ANYONE_HOME_UNIT, True)
			if updated:
				self.anyone_home= True

	def onHeartbeat(self):
		Domoticz.Debug('onHeartbeat called')
		for r in self.active_trackers:
			self.active_trackers[r].heartbeat_handler()
		if self.override.has_expired(self.present_count > 0):
			Domoticz.Status('Override has ended')
			self.override.set_inactive()
			update_domoticz_status(self.OVERRIDE_UNIT, False)

	def onCommand(self, Unit, Command, Level, Hue):
		#only allow the override switch to be operated from gui and only if overrides are enabled
		if Unit == self.OVERRIDE_UNIT:
			if str(Command)=='On':
				if self.override.allow:
					self.override.set_active()
					update_domoticz_status(self.OVERRIDE_UNIT, True)
					self.anyone_home = True
					update_domoticz_status(self.ANYONE_HOME_UNIT, True)
				else:
					Domoticz.Error('Override mode is disabled in configuration. Enable a mode before switching it on.')
			if str(Command)=='Off':
				update_domoticz_status(self.OVERRIDE_UNIT, False)
				self.override.set_inactive()
		return
		
	def onStop(self):
		Domoticz.Debug('onStop called')
#		for r in self.active_trackers:
#			self.active_trackers[r].stop_now()

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()
	
def onStop():
	global _plugin
	_plugin.onStop()

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
