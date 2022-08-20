# Domoticz Python Plugin to monitor tracker for presence/absence of wifi devices without pinging them (pinging can drain your phone battery).
#
# Author: ESCape
#
"""
<plugin key="idetect" name="iDetect multifunctional presence detection" author="ESCape" version="2.1" externallink="https://github.com/d-EScape/Domoticz_iDetect">
	<description>
		<h2>Presence detection by router, ping or other trackers</h2><br/>
		<h3>Authentication settings</h3>
		<ul style="list-style-type:square">
			<li>'Trackers' are devices that can track the presence of 'tags'. For instance: A WiFi device is a type of tag that can be tracked by a WiFi router.</li>
			<li>You can monitor multiple trackers by separating their addresses with a comma. If you don't specify a username, password or other tracker specific setting, then the username and password fields on this page will be used</li>
			<li>Key based authentication will be used if it has been set on the operating system level for the user profile that is running Domoticz (root by default) and on the tracker(s).</li>
			<li>For instructions on how to configure iDetect see the github page. Here are some examples.</li>
		</ul>
			<h4>Example tags:</h4>
			<div style="width:700px; padding: .2em;" class="text ui-widget-content ui-corner-all">phone1=11:22:33:44:55:66, phone2=1A:2B:3C:4D:5E:6F, nas=192.168.1.100#interval=10&amp;ignore=true</div>
			<p>The phones in this example will be tracked by their MAC address. The device called 'nas' will be pinged every 10 seconds but it's presence will be ignored for the 'Anyone home' status.</p>
			<h4>Example trackers:</h4>
			<div style="width:700px; padding: .2em;" class="text ui-widget-content ui-corner-all">192.168.1.1, 192.168.1.55#user=admin&amp;password=mysecret&amp;interval=10</div>
			<p>The first tracker will use default settings and the second one has its own credentials and poll interval set.
			There are many more settings, like tracker types, commands to use etcetera.</p>
		<h3>Behaviour settings</h3>
		<ul style="list-style-type:square">
			<li>'remove obsolete' gives you a choice to automatically delete devices that are no longer in de above list of tags OR to show them as timed-out.</li>
			<li>The grace period should be a multitude of the poll interval in seconds. It controls after how long phones are shown as absent (confirmation from several polls to deal with temporarily dropped connections).</li>
			<li>The override button will let the 'Anyone home' device think there is someone home, even if no presence is detected. This can be helpful for visitors or to take some control over the 'Anyone home' status from other scripts.</li>
			<li>The plugin will automatically determine which command to use if the tracker is a router with a supported wireless interface that can be queried through ssh. If your router (chipset) is not supported you can experiment how to get the right info from the router (or other tracker) and post that info on the forum. 
			Make &amp; Model specific commands can be added to the plugin, but i don't own or know every model, so someone has to provide a working ssh command or other method of getting a list of present tags from a tracker.</li>
		</ul>
		<h3>Is my tracker supported?</h3>
		If it supports ssh, then it is probably supported out-of-the box. Some routers support ssh but have a proprietary command set. If your router is not yet supported and you can figure out which command to use
		it can be easily added to the plugin. Since version 2.0 also other types of trackers can be added to the plugin, like getting pressent MAC addresses from a html page or some type of api. I cannot develop/test 
		a tracker module for devices i don't have acces to, so adding proprietary methods depends on the community (you?), to provide working/tested code or better yet a pull request on github. The (python) code needs to query
		the tracker for connected devices, including everything that is needed to connect and login to the tracker. It might be a simple curl command.
	</description>
	<params>
		<param field="Address" label="Tracker(s)" width="900px" required="true" default="192.168.0.1"/>
		<param field="Username" label="Username" width="200px" required="true" default=""/>
		<param field="Password" label="Password" width="200px" required="false" default="" password="true"/>
		<param field="Mode1" label="Tags to monitor" width="900px" required="true" default="phone1=A1:B1:01:01:01:01,phone2=C2:D2:02:02:02:02"/>
		<param field="Mode6" label="Remove obsolete" width="250px">
			<options>
				<option label="Yes, remove devices" value="True" default="true"/>
				<option label="No, show as unavailable" value="False"/>
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
import helpers.data_helper as data_helper

#
# This class needs to be in plugin.py to interact with (Domoticz) Devices
#
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

#
# Some other Domoticz functions used by the BasePlugin
#
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
		if icon not in Images:
			Domoticz.Debug("Getting icon requested for " + friendly_name + ": " + icon + " from file:" + icon_file[icon])
			newimage = Domoticz.Image(Filename=icon_file[icon])
			newimage.Create()
			Domoticz.Debug("New image: " + str(newimage))
		if icon in Images:
			icon_id=Images[icon].ID
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
		Domoticz.Status("Created device for " + friendly_name + " with unit id " + str(new_unit))
	except:
		Domoticz.Error("FAILED to create device for " + friendly_name + " with unit id " + str(new_unit))
		new_unit = None
	return new_unit
	
def handle_unused_unit(unit, remove_it=False):
	if remove_it:
		Domoticz.Status("Tag " + Devices[unit].Name + " no longer monitored --> removed")
		Devices[unit].Delete()
	else:
		Domoticz.Status("Tag  " + Devices[unit].Name + " no longer monitored --> marked as timed-out")
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
		self.plugin_ready = False
		return

	def onStart(self):
		import sys
		import re
		import subprocess
		from trackers import poll_methods
		from override_switch import override_switch
		
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

		if self.debug:
			Domoticz.Debug('Operation system is: ' + sys.platform)
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
		configured_tags=Parameters["Mode1"].split(",")
		units_in_use=[]
		for tag_config in configured_tags:
			tag_config = tag_config.strip()
			if tag_config.lower().endswith('#ignore'):
				Domoticz.Error('WARNING! Tag uses depricated configuration syntax but might work for now (see manual): ' + tag_config)
				old_style_ignore = True
			else:
				old_style_ignore = False
			try:
				tag_config, tag_options = tag_config.split("#")
			except:
				tag_options = ''
			try:
				friendly_name, tag_id = tag_config.split("=")
				clean_name = friendly_name.strip()
				clean_tag_id = tag_id.strip().upper()
			except:
				Domoticz.Error("Invalid device/tag_id setting: " + str(tag_config))		
			optional = data_helper.options_from_string(tag_options)
			tag_interval=data_helper.custom_or_default(optional, 'interval', self.pollinterval)
			tag_grace=data_helper.custom_or_default(optional, 'grace', self.graceoffline)
			tag_ignore=data_helper.custom_or_default(optional, 'ignore', old_style_ignore)
			
			self.tags_to_monitor[clean_tag_id]=tag_device(clean_tag_id, clean_name, tag_ignore, tag_grace)
			if data_helper.is_ip_address(clean_tag_id):
				Domoticz.Debug('Will use ping tracker to monitor presence for: ' + clean_tag_id)
				if not 'local pinger' in self.active_trackers:
					self.active_trackers['local pinger']=poll_methods['ping']('local pinger', '0', 'irrelevant', 'irrelevant', 'irrelevant', 30)
					self.active_trackers['local pinger'].register_list_interpreter(self.onDataReceive)
				self.active_trackers['local pinger'].register_tag(clean_tag_id, tag_interval)
			units_in_use.append(self.tags_to_monitor[clean_tag_id].domoticz_unit)
			
		Domoticz.Debug("Monitoring " + str(self.tags_to_monitor) + " for presence.")
		self.deleteobsolete = Parameters["Mode6"] == "True"
		
		obsolete_units = []
		for d in Devices:
			if not d in units_in_use:
				if not d in [self.ANYONE_HOME_UNIT, self.OVERRIDE_UNIT]:
					obsolete_units.append(d)
		for obs_unit in obsolete_units:
			handle_unused_unit(obs_unit, self.deleteobsolete)
		
		#parse one or multiple tracker ips from settings
		#Note: the poweroption, username and password are set globally for all trackers!
		Domoticz.Debug('Tracker configuration:' + str(Parameters["Address"]))
		trackerips = Parameters["Address"].strip()
		for tracker in trackerips.split(','):
			try:
				tracker, my_options = tracker.split('#', 1)
			except:
				my_options = ''
			Domoticz.Debug('tracker:' + tracker)
			Domoticz.Debug('options:' + my_options)
			#First get parameters configured using the old style
			if any(e in tracker for e in '=@:') or (my_options != '' and not '=' in my_options):
				Domoticz.Error('WARNING! Tracker uses depricated configuration syntax but will work ... for now (see manual): ' + tracker)	
			my_user=data_helper.get_config_part(tracker, before='@', default=self.trackeruser)
			my_address=data_helper.get_config_part(tracker, after='@', mandatory=True, default='Configuration ERROR!')
			my_port=data_helper.get_config_part(tracker, after=':', default=False)
			my_type=data_helper.get_config_part(tracker, after='=', default='default')
			optional = data_helper.options_from_string(my_options)
			if 'configuration errors' in optional:
				Domoticz.Error(my_address + ' SYNTAX ERROR in configuration: ' + my_options)
				Domoticz.Error('Check documentation on https://github.com/d-EScape/Domoticz_iDetect for correct syntax (it might have changed)')
			my_interval=data_helper.custom_or_default(optional, 'interval', self.pollinterval)
			#Then get parameters configured using the new style (overwriting existing old style)
			my_user=data_helper.custom_or_default(optional, 'user', my_user)
			my_port=data_helper.custom_or_default(optional, 'port', my_port)
			my_type=data_helper.custom_or_default(optional, 'type', my_type)
			my_password=data_helper.custom_or_default(optional, 'password', self.trackerpass)
			my_keyfile=data_helper.custom_or_default(optional, 'keyfile', self.keyfile)
			if 'disabled' in optional and optional['disabled'] == True:
				Domoticz.Status(my_address + ' WARNING Tracker is disabled in configuration:')
			else:
				if 'ssh' in optional:
					my_type = 'prefab'
					self.active_trackers[my_address]=poll_methods[my_type](my_address, my_port, my_user, my_password, my_keyfile, my_interval)
					self.active_trackers[my_address].trackerscript = optional['ssh']
					self.active_trackers[my_address].is_ready = True
				else:
					self.active_trackers[my_address]=poll_methods[my_type](my_address, my_port, my_user, my_password, my_keyfile, my_interval)
				self.active_trackers[my_address].register_list_interpreter(self.onDataReceive)
				Domoticz.Debug('Tracker config:{}, custom port:{}, user:{}, type:{} and options:{}'.format(my_address,my_port,my_user,my_type,data_helper.hide_password_in_list(optional)))
		Domoticz.Debug('Trackers initialized as:' + str(self.active_trackers))
		Domoticz.Debug("Plugin initialization done.")
		self.plugin_ready = True
		Domoticz.Heartbeat(10)
			
	def onDataReceive(self, source):
		Domoticz.Debug('Inbound data from: ' + str(source.tracker_ip) + ' containing ' + str(source.found_tag_ids))
		for seen in source.found_tag_ids:
			if seen in self.tags_to_monitor:
				self.tags_to_monitor[seen].i_see_you()
		self.manage_presence()

	def manage_presence(self):
		if self.override.has_expired(self.present_count > 0):
			Domoticz.Status('Override has ended')
			self.override.set_inactive()
			update_domoticz_status(self.OVERRIDE_UNIT, False)
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
		# Send a heartbeat to the (base)tracker in case a tracker needs a pulse
		# not needed for poll timing, but might be useful when developing custom trackers
		if self.plugin_ready:
			for r in self.active_trackers:
				self.active_trackers[r].heartbeat_handler()
			# Presence is also managed when data is received from a tracker, but we need to make
			# sure it runs every once in a while even if the tracker intervals are long
			self.manage_presence()
		else:
			Domoticz.Status('Skip this hearbeat ... system is still preparing')

	def onCommand(self, Unit, Command, Level, Hue):
		#only allow the override switch to be operated from Domoticz ui and only if overrides are enabled
		#other switches cannot be operated from the Domoticz ui. They are controlled by the plugin
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
		for r in self.active_trackers:
			self.active_trackers[r].stop_now()

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
