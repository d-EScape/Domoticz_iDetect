# On ASUS AiMesh architecture, then "main" router (the one connected to the WAN, even if alone) has a temp file
# that stores all the "clients" connected to the mesh.
# Thanks to Fireport https://www.domoticz.com/forum/viewtopic.php?f=65&t=20467&p=239509&hilit=json+cat+%2Ftmp%2Fclientlist.json#p239509

from trackers.ssh_tracker import ssh_tracker
import helpers.tracker_cli_helper as tracker_cli_helper

class ssh_aimesh_json(ssh_tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.prepare_for_polling()

	def prepare_for_polling(self):
		self.trackerscript = "cat /tmp/clientlist.json"
		self.is_ready = True
