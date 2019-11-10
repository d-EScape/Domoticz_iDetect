import Domoticz
import subprocess
from routers.ssh_router import ssh_router
import helpers.router_cli_helper as router_cli_helper
from datetime import datetime, timedelta
from time import sleep

class ssh_autodetect_generic(ssh_router):
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
		for m in router_cli_helper.generic_methods:
			if m in found_commands:
				build_script = router_cli_helper.generic_methods[m]
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
