# If a tracker module failed to load because of missing requirements then this empty tracker module will load in it's place
# The only thing it does is log an error if a tracker of this type is actually configured

import DomoticzEx
from trackers.tracker_base import tracker

class unavailable_tracker(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if 'tracker_password' in kwargs:
			kwargs['tracker_password']='********'
		DomoticzEx.Debug("Variables passed to the tracker class:" + str(kwargs))
		DomoticzEx.Debug(self.tracker_ip + ' This is a substitude for the actual tracker module that could not be loaded because required python modules are missing')
	