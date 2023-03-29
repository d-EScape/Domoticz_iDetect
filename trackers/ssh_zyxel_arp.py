from trackers.ssh_tracker import ssh_tracker
import helpers.tracker_cli_helper as tracker_cli_helper

class ssh_zyxel_arp(ssh_tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.prepare_for_polling()

	def prepare_for_polling(self):
		self.trackerscript = "ip arp print"
		self.is_ready = True
