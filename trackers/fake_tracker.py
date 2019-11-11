import Domoticz
from trackers.tracker_base import tracker
from time import sleep

class fake_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.prepare_for_polling()
		Domoticz.Debug(self.tracker_ip + ' Is a FAKE tracker, will do a fake poll and rerun fake results')
		
	def poll_present_tag_ids(self):
		sleep(3)
		self.receiver_callback(['11:22:33:44:55:66', '10:20:30:40:50:60', 'Aa:bB:CC:DD:EE:0f'])
	
	def prepare_for_polling(self):
		self.is_ready = True