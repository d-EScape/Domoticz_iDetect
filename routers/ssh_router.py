import Domoticz
import subprocess
from routers.router_base import router
from datetime import datetime, timedelta
from time import sleep

class ssh_router(router):
	def __init__(self, router_ip, router_port, router_user, router_password, router_keyfile, poll_interval):
		super().__init__(router_ip, router_port, router_user, router_password, router_keyfile, poll_interval)
		self.routerscript = ''
		self.sshbin = 'ssh'
		Domoticz.Debug(self.router_ip + ' Router is of the ssh kind')
		
	def poll_present_macs(self):
		Domoticz.Debug(self.router_ip + ' Start pollling and return results to ' + str(self.receiver_callback))
		success, raw_data = self.getfromssh(self.routerscript)
		if not success:
			 self.error_count = self.error_count + 1
			 Domoticz.Log(self.router_ip + ' Could not be polled')
			 return
		self.error_count = 0
		self.receiver_callback(raw_data)

	def prepare_for_polling(self, prep_options={}):
		Domoticz.Debug(self.router_ip + ' Has no prepare_for_pollling function')
		return True
				
	def getfromssh(self, router_cli, alltimeout=5, sshtimeout=3):
		if self.router_password != '':
			Domoticz.Log(self.router_ip + " Using password instead of ssh public key authentication (less secure!)")
			cmd =["sshpass", "-p", self.router_password, self.sshbin, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(self.router_port), self.router_user+"@"+self.router_ip, router_cli]
			Domoticz.Debug(self.router_ip + " Fetching data using: " + " ".join(cmd[:2]) + " **secret** " + " ".join(cmd[3:]))
		else:
			if self.router_keyfile == '':
				cmd =[self.sshbin, "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(self.router_port), self.router_user+"@"+self.router_ip, router_cli]
			else:
				cmd =[self.sshbin, "-i", self.router_keyfile, "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(self.router_port), self.router_user+"@"+self.router_ip, router_cli]
			Domoticz.Debug(self.router_ip + " Fetching data using: " + " ".join(cmd))
		starttime=datetime.now()
		success = True
		try:
			output=subprocess.check_output(cmd, timeout=alltimeout)
			Domoticz.Debug(self.router_ip + " SSH returned:" + str (output))
		except subprocess.CalledProcessError as err:
			Domoticz.Debug(self.router_ip + " SSH subprocess failed with error (" + str(err.returncode) + "):" + str(err))
			success = False
			output = "<Subprocess failed>"
		except subprocess.TimeoutExpired:
			Domoticz.Debug(self.router_ip + " SSH subprocess timeout")
			success = False
			output = "<Timeout>"
		except Exception as err:
			Domoticz.Debug(self.router_ip + " Subprocess failed with error: " + err)
			success = False
			output = "<Unknown error>"
		else:
			if output == "":
				Domoticz.Error(self.router_ip + " Router returned empty response.")
				success = False
				output = "<Empty reponse>"
		timespend=datetime.now()-starttime
		Domoticz.Debug(self.router_ip + " SSH session took " + str(timespend.microseconds//1000) + " milliseconds.")
		return success, output