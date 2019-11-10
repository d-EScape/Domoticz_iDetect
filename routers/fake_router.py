import Domoticz
from routers.router_base import router
from time import sleep

class fake_router(router):
	def __init__(self, router_ip, router_port, router_user, router_password, router_keyfile, poll_interval):
		super().__init__(router_ip, router_port, router_user, router_password, router_keyfile, poll_interval)
		self.prepare_for_polling()
		Domoticz.Debug(self.router_ip + ' Is a FAKE router, will do a fake poll and rerun fake results')
		
	def poll_present_macs(self):
		sleep(3)
		self.receiver_callback(['11:22:33:44:55:66', '10:20:30:40:50:60', 'Aa:bB:CC:DD:EE:0f'])
	
	def prepare_for_polling(self):
		self.is_ready = True