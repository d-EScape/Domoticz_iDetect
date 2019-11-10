import Domoticz
import subprocess
from routers.ssh_router import ssh_router
import helpers.router_cli_helper as router_cli_helper
from datetime import datetime, timedelta
from time import sleep

class ssh_autodetect(ssh_router):
	def __init__(self, router_ip, router_port, router_user, router_password, router_keyfile, poll_interval):
		super().__init__(router_ip, router_port, router_user, router_password, router_keyfile, poll_interval)
		self.prepare_for_polling()
		Domoticz.Debug(self.router_ip + ' router will autodetect ssh cli')

	def prepare_for_polling(self):
		poll_command = []
		build_script = ''
		found_commands = self.find_router_command()
		if found_commands is None:
			self.is_ready = False
			return
		this_router_supports = set(found_commands).intersection(set(router_cli_helper.chipset_methods))
		for supported_command in this_router_supports:
			interfaces = self.find_router_interfaces(supported_command)
			if interfaces is None:
				self.is_ready = False
				return
			else:
				for found in interfaces:
					poll_command.append({'cmd': supported_command, 'interface': found})
					build_script = build_script + router_cli_helper.get_router_cli(supported_command, found) + '\n'
		if build_script == '':
			for m in router_cli_helper.generic_methods:
				if m in found_commands:
					build_script = router_cli_helper.generic_methods[m]
					Domoticz.Debug(self.router_ip + ' Known chipset commands not supported. Using generic mode: ' + m)
					break
		if build_script == '':
			Domoticz.Debug(self.router_ip + ' FAILED No suitable command for polling found on router!')
			self.is_ready = False
			return
		self.routerscript = router_cli_helper.wrap_command(build_script)
		Domoticz.Debug(self.router_ip + ' Poll command(s) string:' + self.routerscript)
		Domoticz.Debug(self.router_ip + ' Ready for pollling')
		self.is_ready = True
		
	def find_router_command(self):
		#The routerscript(s) below will run on the router itself to determine which command and interfaces to use
		detect_cmd_from_router_cli=router_cli_helper.get_try_available_commands_cli()
		success, sshdata=self.getfromssh(detect_cmd_from_router_cli)
		if success:
			foundmethods = sshdata.decode("utf-8")[1:].split("~")
			foundmethods.remove('endoflist')
			Domoticz.Debug("Available commands on " + self.router_ip + ":" + str(foundmethods))
			return foundmethods
		else:
			Domoticz.Debug(self.router_ip + " Could not retreive available commands")
			return None
			
	def find_router_interfaces(self, for_command):
		#find the wifi interfaces for hw specific commands
		#find interfaces suitable for a command (chipset)
		router_command = router_cli_helper.get_try_interface_cli(for_command)
		if router_command == '':
			return None
		success, sshdata=self.getfromssh(router_command)
		if success:
			interfaces = sshdata.decode("utf-8")[1:].split("~")
			Domoticz.Debug(self.router_ip + " Available interfaces for " + for_command + ": " + str(interfaces))
			return interfaces
		else:
			Domoticz.Debug(self.router_ip + " Could not retreive interfaces for " + for_command)
			return None
					
