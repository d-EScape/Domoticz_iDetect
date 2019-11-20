import Domoticz
import threading
import helpers.data_helper as data_helper
from time import sleep
from datetime import datetime, timedelta

class tracker():
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		self.tracker_ip = tracker_ip
		self.tracker_port = tracker_port
		self.tracker_user = tracker_user
		self.tracker_password = tracker_password
		self.tracker_keyfile = tracker_keyfile
		self.poll_interval = poll_interval
		self.tag_type = 'mac_address'
		self.found_tag_ids = []
		self.last_update = datetime.now()
		self.error_state = False
		self.is_ready = False
		self.poll_timer = None
		self.interpreter_callback = None
		self.error_count = 0
		self.poll_thread = None
		self.poll_timer = threading.Timer(self.poll_interval, self.timer_clockwork)
		self.poll_timer.start()
			
	def heartbeat_handler(self):
		#don't need heartbeat when using threading timers
		if True:
			return
			
	def poll_present_tag_ids(self):
		#placeholder in case subclass misses this method
		Domoticz.Debug(self.tracker_ip + ' Class has no polling method defined')
	
	def receiver_callback(self, raw_data):
		self.found_tag_ids = data_helper.clean_tag_id_list(raw_data, self.tag_type)
		if not self.interpreter_callback is None:
			self.interpreter_callback(self)
		else:
			Domoticz.Debug(self.tracker_ip + ' No interpreter_callback registered. Ignoring new data.')
				
	def timer_clockwork(self):
		if self.is_ready:
			Domoticz.Debug(self.tracker_ip + ' Timed poll starting like clockwork')
			self.poll_present_tag_ids()
		else:
			Domoticz.Log(self.tracker_ip + ' Not (yet) ready for polling')
		self.poll_timer = threading.Timer(self.poll_interval, self.timer_clockwork)
		self.poll_timer.start()
		
	def stop_now(self):
		self.is_ready = False
		if not self.poll_timer is None:
			self.poll_timer.cancel()
			self.poll_timer.join()
			Domoticz.Debug(self.tracker_ip + ' Poll timer canceled')
	
	def register_list_interpreter(self, callback):
		self.interpreter_callback=callback
		Domoticz.Debug(self.tracker_ip + ' Data will be received and interpreted by ' + str(self.interpreter_callback))
		