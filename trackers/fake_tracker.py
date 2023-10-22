# Example of a very simple tracker. It returns fake results and can also be used for testing.
# The __init__() method should call the super()._init__() method with all the arguments, so the tracker_base
# is properly created. The tracker_base will hold of all the (generic) variables for the tracker object, so you don't
# have to.
# The tracker_base also takes care of the polling interval and data parsing, so the router specific module can
# be quite simple. It only needs a method for polling and return its data to the receiver_callback of
# the tracker_base. The data can be a list (containing tag addresses - for now MAC or IP), but it can also be
# a string. The receiver_callback will search for valid addresses in the (dirty) string.
# Please do not modify tracker_base unless the change is an enhancement for every kind of
# tracker. You can always expand upon the tracker_base by including one of its methods in your tracker class AND 
# calling the super().<methodname> to execute both.
#
# self.is_ready variable has to be set to True by your own tracker class or it will never poll.
#
# If your tracker uses any kind of background thread/connection make sure you end/close it using a
# stop_now(self) method and add super().stop_now() at the end. Domoticz will hang if you don't and try to stop the hardware!
# See ssh_tracker for an example.
# If you want to create a tracker that uses ssh you should base it on the ssh_tracker (which itself is again based on tracker_base)
# See (amongst others) ssh_routeros.py for an example on how simple it can be.
#
# Last but not least: add your tracker class to __init__.py in the trackers directory, otherwise it will not be known to the plugin.

import DomoticzEx
from trackers.tracker_base import tracker

class fake_tracker(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.prepare_for_polling()
		DomoticzEx.Debug(self.tracker_ip + ' Is a FAKE tracker, will do a fake poll and return fake results')
		
	def poll_present_tag_ids(self):
		# Add code to retrieve data from a tracker and return the (raw string of formatted list) data to
		# the receiver_callback that is in the base_tracker
#		self.receiver_callback(['11:22:33:44:55:66', '10:20:30:40:50:60', 'Aa:bB:CC:DD:EE:0f'])
		self.receiver_callback('this is a text with some 11:22:33:44:55:66 mac addresses 10:20:30:40:50:60. It should find 3 of them Aa-bB-CC-DD-EE-0f, even if formatted differently')
		# This would also work:
		#self.receiver_callback('i am a string with some 11:22:33:44:55:66 addrresses and other 10:20:30:40:50:60 unusable text that will be ignored Aa:bB:CC:DD:EE:0f addresses may be upper or lower case')
	
	def prepare_for_polling(self):
		# This metod is not required but setting self.is_true is.
		self.is_ready = True
