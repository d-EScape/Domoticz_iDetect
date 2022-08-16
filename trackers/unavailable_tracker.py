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

import Domoticz
from trackers.tracker_base import tracker

class unavailable_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		Domoticz.Error(self.tracker_ip + ' The trackertype is not supported until you install the required python modules')
	