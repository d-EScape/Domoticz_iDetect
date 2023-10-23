import DomoticzEx
import subprocess
import helpers.data_helper as data_helper
from trackers.tracker_base import tracker
import helpers.data_helper as data_helper
from datetime import datetime, timedelta
from time import sleep
from pssh.clients.ssh import SSHClient
	
class ssh_tracker(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.trackerscript = ''
		self.connected = False
		if self.tracker_port is None:
			self.tracker_port = 22

		DomoticzEx.Debug(self.tracker_ip + ' Tracker is of the ssh kind')
		self.ssh_connect()
			
	def logger(self,message):
		DomoticzEx.Log(message)

	def poll_present_tag_ids(self):
		DomoticzEx.Debug(self.tracker_ip + ' Start poll and return results to ' + str(self.receiver_callback))
		success, raw_data = self.getfromssh(self.trackerscript)
		if not success:
			self.error_count = self.error_count + 1
			DomoticzEx.Log(self.tracker_ip + ' Could not be polled')
			return
		else:
			self.error_count = 0
			self.receiver_callback(raw_data)

	def prepare_for_polling(self):
		#Should be implemented in specfic tracker
		DomoticzEx.Debug(self.tracker_ip + ' Has no prepare_for_pollling method.')
		return True

	def ssh_connect(self):
		DomoticzEx.Debug(self.tracker_ip + ' ====> SSHClient start connect on port ' + str(self.tracker_port))
		if self.tracker_password == '':
			if self.tracker_keyfile != '':
				my_key_file = self.tracker_keyfile
				DomoticzEx.Debug(self.tracker_ip + ' ====> SSH using key: ' + my_key_file)
				try:
					self.client = SSHClient(self.tracker_ip, port=self.tracker_port, user=self.tracker_user, pkey=self.tracker_keyfile, timeout=5)
				except Exception as e:
					DomoticzEx.Error(self.tracker_ip + ' SSH Could not connect (using custom key file). Exception: ' + str(e))
					self.connected = False
					return
			else:
				try:
					self.client = SSHClient(self.tracker_ip, port=self.tracker_port, user=self.tracker_user, pkey='~/.ssh/id_rsa', timeout=5)
				except Exception as e:
					DomoticzEx.Error(self.tracker_ip + ' SSH Could not connect (with os key). Exception: ' + str(e))
					self.connected = False
					return False
		else:
			try:
				self.client = SSHClient(self.tracker_ip, port=self.tracker_port, user=self.tracker_user, password=self.tracker_password, timeout=5)
			except Exception as e:
				DomoticzEx.Error(self.tracker_ip + ' ====> SSH Could not connect (using password). Exception: ' + str(e))
				self.connected = False
				return False
		DomoticzEx.Status(self.tracker_ip + ' ====> SSH connection established')
		self.connected = True
		return True

	def getfromssh(self, tracker_cli, alltimeout=5, sshtimeout=3):
		DomoticzEx.Debug(self.tracker_ip + " ====> SSH Fetching data using: " + tracker_cli)
		starttime=datetime.now()
		if not self.connected:
			DomoticzEx.Debug(self.tracker_ip + ' ====> SSH not connected ... connecting')
			self.ssh_connect()
		if not self.connected:
			return False, ''
		try:
			output = self.client.run_command(tracker_cli, read_timeout=5)
			ssh_output='\n'.join(map(str,output.stdout))
			DomoticzEx.Debug(self.tracker_ip + ' ====> SSH returned (decoded):' + ssh_output)
		except Exception as e:
			DomoticzEx.Error(self.tracker_ip + ' ====> SSH failed with exception: ' + str(e))
			try:
				self.disconnect()
				DomoticzEx.Status(self.tracker_ip + ' ====> SSH resetting connection')
			except:
				DomoticzEx.Debug(self.tracker_ip + ' ====> SSH connection reset failed')
			self.connected = False
			return False, ''
		timespend=datetime.now()-starttime
		DomoticzEx.Debug(self.tracker_ip + " ====> SSH session took " + str(timespend.microseconds//1000) + " milliseconds.")
		return True, ssh_output

	def stop_now(self):
		self.is_ready = False
		try:
			self.client.disconnect()
			DomoticzEx.Debug(self.tracker_ip + ' ====> SSH client disconnected')
		except:
			DomoticzEx.Debug(self.tracker_ip + ' ====> Unable to disconnect SSH session')
		self.client=None
		super().stop_now()
