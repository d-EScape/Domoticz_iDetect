import Domoticz
from trackers.tracker_base import tracker
import threading
import os
import sys

class ping_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.default_interval = poll_interval
		self.tag_type = 'ip_address'
		self.prepare_for_polling()
		self.ping_timer = {}

	def register_tag(self, new_tag, tag_interval=None):
		if tag_interval is None:
			tag_interval = self.default_interval
		Domoticz.Debug(self.tracker_ip + ' Starting ping timer for ' + new_tag)
		self.ping_timer[new_tag] = threading.Timer(tag_interval, self.ping_clockwork, [new_tag, tag_interval])
		self.ping_timer[new_tag].start()
		
	def ping_clockwork(self, tag_id, interval):
		if self.can_be_pinged(tag_id):
			online = True
		else:
			online = False
		self.ping_timer[tag_id] = threading.Timer(interval, self.ping_clockwork, [tag_id, interval])
		self.ping_timer[tag_id].start()
		if online:
			self.receiver_callback(tag_id)
				
	def poll_present_tag_ids(self):
		# The ping tracker needs no poll method. Every tag has it's own timer
		# This method could be used as a heartbeat
		return
		
	def prepare_for_polling(self):
		if sys.platform in ['win32']:
			self.ping_command = 'ping -n 1 -w 100 '
		else:
			self.ping_command = 'ping -c1 -W1 '
		self.is_ready = True
	
	def can_be_pinged(self, tagged_host):
		error_level = os.system(self.ping_command + tagged_host)
		Domoticz.Debug('Tried pinging tag: ' + tagged_host + ' --> error_level (0 means online): ' + str(error_level))
		return not error_level
		
	def stop_now(self):
		self.is_ready = False
		for tmr in self.ping_timer:
			Domoticz.Debug(self.tracker_ip + ' Stopping ping timer for ' + tmr)
			self.ping_timer[tmr].cancel()
		for tmr in self.ping_timer:
			self.ping_timer[tmr].join()
		super().stop_now()