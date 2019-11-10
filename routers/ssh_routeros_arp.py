from routers.ssh_router import ssh_router
import helpers.router_cli_helper as router_cli_helper

class ssh_routeros_arp(ssh_router):
	def __init__(self, router_ip, router_port, router_user, router_password, router_keyfile, poll_interval):
		super().__init__(router_ip, router_port, router_user, router_password, router_keyfile, poll_interval)
		self.prepare_for_polling()

	def prepare_for_polling(self):
		functional_part = "ip arp print"
		self.routerscript = router_cli_helper.wrap_command(functional_part)
		self.is_ready = True
