import Domoticz
from trackers.ssh_tracker import ssh_tracker
import helpers.tracker_cli_helper as tracker_cli_helper

class ssh_autodetect_generic(ssh_tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.prepare_for_polling()
		Domoticz.Debug(self.tracker_ip + ' tracker will autodetect ssh cli')
		
	def prepare_for_polling(self):
		build_script = ''
		self.command_support = self.find_tracker_command()
		if self.command_support is None:
			self.is_ready = False
			return
		for generic_command in tracker_cli_helper.generic_method_order:
			if generic_command in self.command_support:
				build_script = tracker_cli_helper.get_tracker_cli(generic_command, self.command_support[generic_command])
				break
		if build_script == '':
			Domoticz.Debug(self.tracker_ip + ' FAILED: No suitable polling command found on this tracker!')
			self.is_ready = False
			return
		self.trackerscript = build_script
		Domoticz.Debug(self.tracker_ip + ' Prepared to poll using: ' + self.trackerscript)
		self.is_ready = True

	def find_tracker_command(self):
		#Run a script on the tracker itself to determine which command to use
		command_path = {}
		detect_cmd_from_tracker_cli=tracker_cli_helper.get_try_available_commands_cli()
		success, sshdata=self.getfromssh(detect_cmd_from_tracker_cli)
		if success:
			for this_line in sshdata.splitlines():
				if not this_line.endswith("not found"):
					cmd = this_line.split(" ")[0]
					if cmd in tracker_cli_helper.generic_methods:
						full_cmd = this_line.split(" ")[-1]
						command_path[cmd] = full_cmd
			Domoticz.Debug("Available generic commands on " + self.tracker_ip + ":" + str(command_path))
			return command_path
		else:
			Domoticz.Debug(self.tracker_ip + " Could not retreive available generic commands")
			return None