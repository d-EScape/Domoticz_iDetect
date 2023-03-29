# This tracker type sole purpose is to test error handling when loading tracker modules

import Domoticz
import NonExistingStuff as NotGonnaWork
from trackers.tracker_base import tracker

class test_error_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.prepare_for_polling()
		Domoticz.Log(self.tracker_ip + ' Just testing an import error.')
		
	def poll_present_tag_ids(self):
		self.receiver_callback('this is a text with some 11:22:33:44:55:66 mac addresses 10:20:30:40:50:60. It should find 3 of them Aa-bB-CC-DD-EE-0f, even if formatted differently')
	
	def prepare_for_polling(self):
		self.is_ready = True
