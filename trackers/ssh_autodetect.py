import Domoticz
from trackers.ssh_tracker import ssh_tracker
import helpers.tracker_cli_helper as tracker_cli_helper

class ssh_autodetect(ssh_tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.prepare_for_polling()
		self.command_support = {}
		Domoticz.Debug(self.tracker_ip + ' tracker will autodetect ssh cli')

	def prepare_for_polling(self):
		build_script = ''
		self.command_support = self.find_tracker_command()
		if self.command_support is None:
			self.is_ready = False
			return
		for supported_command in tracker_cli_helper.chipset_methods:
			if supported_command in self.command_support:
				interfaces = self.find_tracker_interfaces(supported_command)
				if interfaces is None:
					continue
				else:
					for found_interface in interfaces:
						build_script = build_script + tracker_cli_helper.get_tracker_cli(supported_command, self.command_support[supported_command], found_interface)
		if build_script == '':
			for generic_command in tracker_cli_helper.generic_method_order:
				if generic_command in self.command_support:
					build_script = tracker_cli_helper.get_tracker_cli(generic_command, self.command_support[generic_command])
					Domoticz.Status(self.tracker_ip + ' No supported chipset found. Using generic mode: ' + generic_command)
					break
		if build_script == '':
			Domoticz.Debug(self.tracker_ip + ' FAILED: No suitable polling command found on this tracker!')
			self.is_ready = False
			return
		self.trackerscript = tracker_cli_helper.wrap_command(build_script)
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
					if cmd in tracker_cli_helper.chipset_methods or cmd in tracker_cli_helper.generic_methods:
						full_cmd = this_line.split(" ")[-1]
						command_path[cmd] = full_cmd
			Domoticz.Debug("Available commands on " + self.tracker_ip + ":" + str(command_path))
			return command_path
		else:
			Domoticz.Debug(self.tracker_ip + " Could not retreive available commands")
			return None

	def find_tracker_interfaces(self, for_command):
		#Run a script on the tracker itself to determine which interfaces can be queried using the command
		tracker_command = tracker_cli_helper.get_try_interface_cli(for_command, self.command_support[for_command])
		if tracker_command == '':
			return None
		success, sshdata=self.getfromssh(tracker_command)
		if success:
			interfaces = sshdata[1:].split("~")
			Domoticz.Debug(self.tracker_ip + " Available interfaces for " + for_command + ": " + str(interfaces))
			return interfaces
		else:
			Domoticz.Debug(self.tracker_ip + " Could not retreive interfaces for " + for_command)
			return None
