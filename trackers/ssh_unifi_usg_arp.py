from trackers.ssh_tracker import ssh_tracker
import helpers.tracker_cli_helper as tracker_cli_helper

class ssh_unifi_usg_arp(ssh_tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.prepare_for_polling()

	def prepare_for_polling(self):
		self.trackerscript = "show arp"
		self.is_ready = True
