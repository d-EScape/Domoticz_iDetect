import DomoticzEx
import threading
import helpers.data_helper as data_helper
from time import sleep
from datetime import datetime, timedelta

class tracker():
	def __init__(self, *args, **kwargs):
		DomoticzEx.Debug("Arguments passed to tracker (except password):" + str({x: kwargs[x] for x in kwargs if x not in ['tracker_password']}))
		self.debug = kwargs.get('debug', False)
		self.tracker_ip = kwargs.get('tracker_ip')
		self.tracker_port = kwargs.get('tracker_port')
		self.tracker_user = kwargs.get('tracker_user')
		self.tracker_password = kwargs.get('tracker_password')
		self.tracker_keyfile = kwargs.get('tracker_keyfile')
		self.poll_interval = kwargs.get('poll_interval')
		self.tag_type = 'mac_address'
		self.found_tag_ids = []
		self.last_update = datetime.now()
		self.error_state = False
		self.is_ready = False
		self.stop = False
		self.poll_timer = None
		self.interpreter_callback = None
		self.error_count = 0
		self.poll_thread = None
		self.poll_timer = threading.Timer(self.poll_interval, self.timer_clockwork)
		self.poll_timer.start()
		DomoticzEx.Status('Starting address:{}, port:{}, user:{}, keyfile:{}, class:{} and poll interval:{}'.format(self.tracker_ip, self.tracker_port, self.tracker_user, self.tracker_keyfile, self.__class__.__qualname__, self.poll_interval))
			
	def heartbeat_handler(self):
		# don't need heartbeat when using threading timers
		# run some extra checks for beta debugging
		if self.poll_timer is None:
			DomoticzEx.Debug(self.tracker_ip + ' Does not seem to have a poll timer')
		return
			
	def poll_present_tag_ids(self):
		#placeholder in case subclass misses this method
		DomoticzEx.Debug(self.tracker_ip + ' Class has no polling method defined')
	
	def receiver_callback(self, raw_data):
		DomoticzEx.Debug(self.tracker_ip + ' Sent RAW:' + str(raw_data))
		self.found_tag_ids = data_helper.clean_tag_id_list(raw_data, self.tag_type)
		if not self.interpreter_callback is None:
			self.interpreter_callback(self)
		else:
			DomoticzEx.Debug(self.tracker_ip + ' No interpreter_callback registered. Ignoring new data.')
				
	def timer_clockwork(self):
		if self.is_ready:
			DomoticzEx.Debug(self.tracker_ip + ' Timed poll starting like clockwork. '  + str(threading.active_count()) + " threads active (including me)")
			self.poll_present_tag_ids()
		else:
			DomoticzEx.Log(self.tracker_ip + ' Not (yet) ready for polling')
			DomoticzEx.Debug('Using address:{}, port:{}, user:{}, keyfile:{}, class:{} and poll interval:{}'.format(self.tracker_ip, self.tracker_port, self.tracker_user, self.tracker_keyfile, self.__class__.__qualname__, self.poll_interval))
		if not self.stop:
			self.poll_timer = threading.Timer(self.poll_interval, self.timer_clockwork)
			self.poll_timer.start()
		
	def stop_now(self):
		self.stop = True
		self.is_ready = False
		DomoticzEx.Debug("{} main tracker stopping".format(self.tracker_ip))
		if not self.poll_timer is None:
			self.poll_timer.cancel()
			self.poll_timer.join()
			DomoticzEx.Debug("{} Poll timer canceled and job finished".format(self.tracker_ip))
		DomoticzEx.Debug("{} main tracker stopped".format(self.tracker_ip))
	
	def register_list_interpreter(self, callback):
		self.interpreter_callback=callback
		DomoticzEx.Debug(self.tracker_ip + ' Data will be received and interpreted by ' + str(self.interpreter_callback))
		