import helpers.data_helper as data_helper
from datetime import datetime

class override_switch():
	def __init__(self, mode):
		self.start_time = datetime.now()
		self.active = False
		self.allow=True
		self.indefinitely = False
		self.reset_on_presence = True
		self.duration=None
		
		if mode == "No":
			self.allow=False
		elif mode == "Next":
			self.reset_on_presence = True
			self.indefinitely = False
		elif mode == "Forever":
			self.indefinitely = True
		else:
			self.duration=int(mode) * 3600
			self.reset_on_presence = False
			
	def set_active(self):
		if self.allow:
			self.start_time = datetime.now()
			self.active = True
			return True
		else:
			return False
		
	def set_inactive(self):
		self.active = False
			
	def has_expired(self, anyone_home=False):
		if not self.active:
			return False
		if self.indefinitely:
			return False
		if self.active and self.reset_on_presence and anyone_home:
			return True
		if self.active and not self.duration is None:
			if data_helper.time_since_last(self.start_time) > self.duration:
				return True
		return False