import Domoticz
import subprocess
from trackers.ssh_tracker import ssh_tracker
import helpers.tracker_cli_helper as tracker_cli_helper
from datetime import datetime, timedelta
from time import sleep

class ssh_autodetect_generic(ssh_tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.prepare_for_polling()
		Domoticz.Debug(self.tracker_ip + ' tracker will autodetect ssh cli')

	def prepare_for_polling(self):
		poll_command = []
		build_script = ''
		found_commands = self.find_tracker_command()
		if found_commands is None:
			self.is_ready = False
			return
		for m in tracker_cli_helper.generic_methods:
			if m in found_commands:
				build_script = tracker_cli_helper.generic_methods[m]
				break
		if build_script == '':
			Domoticz.Debug(self.tracker_ip + ' FAILED No suitable command for polling found on tracker!')
			self.is_ready = False
			return
		self.trackerscript = tracker_cli_helper.wrap_command(build_script)
		Domoticz.Debug(self.tracker_ip + ' Poll command(s) string:' + self.trackerscript)
		Domoticz.Debug(self.tracker_ip + ' Ready for pollling')
		self.is_ready = True
		
	def find_tracker_command(self):
		#The trackerscript(s) below will run on the tracker itself to determine which command and interfaces to use
		detect_cmd_from_tracker_cli=tracker_cli_helper.get_try_available_commands_cli()
		success, sshdata=self.getfromssh(detect_cmd_from_tracker_cli)
		if success:
			foundmethods = sshdata.decode("utf-8")[1:].split("~")
			foundmethods.remove('endoflist')
			Domoticz.Debug("Available commands on " + self.tracker_ip + ":" + str(foundmethods))
			return foundmethods
		else:
			Domoticz.Debug(self.tracker_ip + " Could not retreive available commands")
			return None
