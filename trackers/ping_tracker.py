import Domoticz
from trackers.tracker_base import tracker
import socket
import os

class ping_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.tags_to_ping = []
		Domoticz.Debug(self.tracker_ip + ' Tracker will ping hosts from local system.')
		self.prepare_for_polling()
		
	def register_tag(self, new_tag):
		self.tags_to_ping.append(new_tag)
		Domoticz.Debug('Registered pingable tags: ' + str(self.tags_to_ping))
		
	def poll_present_tag_ids(self):
		Domoticz.Debug(self.tracker_ip + ' Start pinging and return results to ' + str(self.receiver_callback))
		online_tags = []
		for this_tag in self.tags_to_ping:
			if self.can_be_pinged(this_tag):
				online_tags.append(this_tag)
		self.receiver_callback(online_tags)

	def prepare_for_polling(self):
		self.is_ready = True
	
	def can_be_pinged(self, tagged_host):
		error_level = os.system("ping -c1 -W1 " + tagged_host)
		Domoticz.Debug('Tried pinging tag: ' + tagged_host + ' --> error_level: ' + str(error_level))
		return not error_level
	
# 	def sort_of_ping(ip, port=):
# 		socket.setdefaulttimeout(0.5)
# 		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 		try:
# 			sock.connect((ip, port))
# 	#	except socket.error:
# 		except:
# 			sock.close()
# 			return False
# 		sock.close()
# 		return True