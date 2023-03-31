import Domoticz
import threading
import helpers.data_helper as data_helper
from time import sleep
from datetime import datetime, timedelta

class tracker():
	def __init__(self, *args, **kwargs):
		self.tracker_ip = kwargs.get('tracker_ip')
		self.tracker_port = kwargs.get('tracker_port')
		self.tracker_user = kwargs.get('tracker_user')
		self.tracker_password = kwargs.get('tracker_password')
		self.tracker_keyfile = kwargs.get('tracker_keyfile')
		self.poll_interval = kwargs.get('poll_interval')
		self.tag_type = 'mac_address'
		self.found_tag_ids = []
		self.last_update = datetime.now()
		self.last_init = datetime.now()
		self.error_state = False
		self.is_ready = False
		self.stop = False
		self.poll_timer = None
		self.interpreter_callback = None
		self.error_count = 0
		self.initcount = 6
		self.poll_thread = None
		self.poll_timer = threading.Timer(self.poll_interval, self.timer_clockwork)
		self.poll_timer.start()
		Domoticz.Status('Starting address:{}, port:{}, user:{}, keyfile:{}, class:{} and poll interval:{}'.format(self.tracker_ip, self.tracker_port, self.tracker_user, self.tracker_keyfile, self.__class__.__qualname__, self.poll_interval))
			
	def heartbeat_handler(self):
		# don't need heartbeat when using threading timers
		# run some extra checks for beta debugging
		if self.poll_timer is None:
			Domoticz.Debug(self.tracker_ip + ' Does not seem to have a poll timer')
		return
		
	def prepare_for_polling(self):
		#Should be implemented in specfic tracker
		Domoticz.Debug(self.tracker_ip + ' Has no prepare_for_pollling method.')
		self.is_ready = True
		return True
			
	def poll_present_tag_ids(self):
		#placeholder in case subclass misses this method
		Domoticz.Debug(self.tracker_ip + ' Class has no polling method defined')
	
	def receiver_callback(self, raw_data):
		Domoticz.Debug(self.tracker_ip + ' Sent RAW:' + str(raw_data))
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
			Domoticz.Log(self.tracker_ip + ' Not (yet) fully initialized for polling')
			Domoticz.Debug('Tracker address:{}, port:{}, user:{}, keyfile:{}, class:{} and poll interval:{}'.format(self.tracker_ip, self.tracker_port, self.tracker_user, self.tracker_keyfile, self.__class__.__qualname__, self.poll_interval))
			retrywait = ( 1 + ( 6 - self.initcount)) * 15
			if self.initcount > 0 and (datetime.now() - self.last_init).seconds > retrywait:
				Domoticz.Status("{} tracker initialization (still) not completed after waiting at least {} seconds. Retrying {} more times".format(self.tracker_ip, retrywait, self.initcount))
				self.last_init = datetime.now()
				self.initcount = self.initcount - 1
				self.prepare_for_polling()
		if not self.stop:
			Domoticz.Debug('{} keep the clockwork ticking'.format(self.tracker_ip))
			self.poll_timer = threading.Timer(self.poll_interval, self.timer_clockwork)
			self.poll_timer.start()
		else:
			Domoticz.Debug('{} clockwork stopped'.format(self.tracker_ip))
		
	def stop_now(self):
		self.stop = True
		self.is_ready = False
		Domoticz.Debug("{} main tracker stopping".format(self.tracker_ip))
		if not self.poll_timer is None:
			self.poll_timer.cancel()
			self.poll_timer.join()
			Domoticz.Debug("{} Poll timer canceled and job finished".format(self.tracker_ip))
		Domoticz.Debug("{} main tracker stopped".format(self.tracker_ip))
	
	def register_list_interpreter(self, callback):
		self.interpreter_callback=callback
		Domoticz.Debug(self.tracker_ip + ' Data will be received and interpreted by ' + str(self.interpreter_callback))
		