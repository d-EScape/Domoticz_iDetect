import Domoticz
from trackers.tracker_base import tracker
from datetime import datetime
#import socket
import os

class ping_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.default_interval = poll_interval
		self.tags_to_ping = {}
		self.tags_last_ping = {}
		self.prepare_for_polling()
		
	def time_since_last(self, past_moment):
		number_of_seconds = (datetime.now() - past_moment).total_seconds()
		return number_of_seconds
		
	def register_tag(self, new_tag, tag_interval=None):
		if tag_interval is None:
			tag_interval = self.default_interval
		self.tags_to_ping[new_tag]=tag_interval
		self.tags_last_ping[new_tag]=datetime.now()
		
	def poll_present_tag_ids(self):
		online_tags = []
		for this_tag in self.tags_to_ping:
			seconds_ago = self.time_since_last(self.tags_last_ping[this_tag])
			if seconds_ago > self.tags_to_ping[this_tag]:
				if self.can_be_pinged(this_tag):
					online_tags.append(this_tag)
				self.tags_last_ping[this_tag]=datetime.now()
		if len(online_tags) > 0:
			self.receiver_callback(online_tags)

	def prepare_for_polling(self):
		self.is_ready = True
	
	def can_be_pinged(self, tagged_host):
		error_level = os.system("ping -c1 -W1 " + tagged_host)
		Domoticz.Debug('Tried pinging tag: ' + tagged_host + ' --> error_level (0 means online): ' + str(error_level))
		return not error_level