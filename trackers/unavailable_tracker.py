# If a tracker module failed to load because of missing requirements then this empty tracker module will load in it's place
# The only thing it does is log an error if a tracker of this type is actually configured
# This approach ensures that no errors are generated on missing requirements for tracker types that are not even in use.

import Domoticz
from trackers.tracker_base import tracker

class unavailable_tracker(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		Domoticz.Debug(self.tracker_ip + ' This is a substitude for the actual tracker module that could not be loaded because required python modules are missing')
	