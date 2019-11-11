import Domoticz
import subprocess
from trackers.tracker_base import tracker
from datetime import datetime, timedelta
from time import sleep

class ssh_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.trackerscript = ''
		self.sshbin = 'ssh'
		Domoticz.Debug(self.tracker_ip + ' Tracker is of the ssh kind')
		
	def poll_present_tag_ids(self):
		Domoticz.Debug(self.tracker_ip + ' Start pollling and return results to ' + str(self.receiver_callback))
		success, raw_data = self.getfromssh(self.trackerscript)
		if not success:
			 self.error_count = self.error_count + 1
			 Domoticz.Log(self.tracker_ip + ' Could not be polled')
			 return
		self.error_count = 0
		self.receiver_callback(raw_data)

	def prepare_for_polling(self):
		Domoticz.Debug(self.tracker_ip + ' Has no prepare_for_pollling function')
		return True
				
	def getfromssh(self, tracker_cli, alltimeout=5, sshtimeout=3):
		if self.tracker_password != '':
			Domoticz.Log(self.tracker_ip + " Using password instead of ssh public key authentication (less secure!)")
			cmd =["sshpass", "-p", self.tracker_password, self.sshbin, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(self.tracker_port), self.tracker_user+"@"+self.tracker_ip, tracker_cli]
			Domoticz.Debug(self.tracker_ip + " Fetching data using: " + " ".join(cmd[:2]) + " **secret** " + " ".join(cmd[3:]))
		else:
			if self.tracker_keyfile == '':
				cmd =[self.sshbin, "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(self.tracker_port), self.tracker_user+"@"+self.tracker_ip, tracker_cli]
			else:
				cmd =[self.sshbin, "-i", self.tracker_keyfile, "-o", "ConnectTimeout=" + str(sshtimeout), '-p'+str(self.tracker_port), self.tracker_user+"@"+self.tracker_ip, tracker_cli]
			Domoticz.Debug(self.tracker_ip + " Fetching data using: " + " ".join(cmd))
		starttime=datetime.now()
		success = True
		try:
			output=subprocess.check_output(cmd, timeout=alltimeout)
			Domoticz.Debug(self.tracker_ip + " SSH returned:" + str (output))
		except subprocess.CalledProcessError as err:
			Domoticz.Debug(self.tracker_ip + " SSH subprocess failed with error (" + str(err.returncode) + "):" + str(err))
			success = False
			output = "<Subprocess failed>"
		except subprocess.TimeoutExpired:
			Domoticz.Debug(self.tracker_ip + " SSH subprocess timeout")
			success = False
			output = "<Timeout>"
		except Exception as err:
			Domoticz.Debug(self.tracker_ip + " Subprocess failed with error: " + err)
			success = False
			output = "<Unknown error>"
		else:
			if output == "":
				Domoticz.Error(self.tracker_ip + " Tracker returned empty response.")
				success = False
				output = "<Empty reponse>"
		timespend=datetime.now()-starttime
		Domoticz.Debug(self.tracker_ip + " SSH session took " + str(timespend.microseconds//1000) + " milliseconds.")
		return success, output