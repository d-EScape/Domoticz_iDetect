import DomoticzEx
import subprocess
import helpers.data_helper as data_helper
from trackers.tracker_base import tracker
import helpers.data_helper as data_helper
from datetime import datetime, timedelta
from time import sleep
import paramiko
	
class ssh_tracker(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.trackerscript = ''
		self.connected = False
		if self.tracker_port is None:
			self.tracker_port = 22
		self.client = paramiko.SSHClient()
		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
				rsa_key = None
				try:
					rsa_key=paramiko.RSAKey.from_private_key_file(my_key_file)
				except Exception as e:
					DomoticzEx.Error(self.tracker_ip + ' ====> SSH Could not get RSA from private key. Exception: ' + str(e))
				DomoticzEx.Debug(self.tracker_ip + ' ====> SSH using key: ' + str(my_key_file))
				try:
					self.client.connect(self.tracker_ip, port=self.tracker_port, username=self.tracker_user, pkey=rsa_key, timeout=5)
				except Exception as e:
					DomoticzEx.Error(self.tracker_ip + ' SSH Could not connect (using custom key file). Exception: ' + str(e))
					self.connected = False
					return
			else:
				try:
					self.client.connect(self.tracker_ip, port=self.tracker_port, username=self.tracker_user, timeout=5)
				except Exception as e:
					DomoticzEx.Error(self.tracker_ip + ' SSH Could not connect (with os key). Exception: ' + str(e))
					self.connected = False
					return False
		else:
			try:
				self.client.connect(self.tracker_ip, port=self.tracker_port, username=self.tracker_user, password=self.tracker_password, look_for_keys=False, timeout=5)
			except Exception as e:
				DomoticzEx.Error(self.tracker_ip + ' ====> SSH Could not connect (using password). Exception: ' + str(e))
				self.connected = False
				return False
		try:
			self.my_transport = self.client.get_transport()
			DomoticzEx.Status(self.tracker_ip + ' ====> SSH connection established')
		except:
			DomoticzEx.Error(self.tracker_ip + ' ====> SSH connection failed (no transport)')
			self.connected = False
			return False
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
			stdin, stdout, stderr = self.client.exec_command(tracker_cli, timeout=5)
			ssh_output = stdout.read().decode("utf-8")
			ssh_error = stderr.read().decode("utf-8")
			if ssh_error != '':
				DomoticzEx.Error(self.tracker_ip + ' ====> SSH returned error:' + ssh_error)
			DomoticzEx.Debug(self.tracker_ip + ' ====> SSH returned (decoded):' + ssh_output)
		except Exception as e:
			DomoticzEx.Error(self.tracker_ip + ' ====> SSH failed with exception: ' + str(e))
			DomoticzEx.Debug(self.tracker_ip + " ====> SSH tried for " + str((datetime.now()-starttime).microseconds//1000) + " milliseconds.")
			try:
				self.client.close()
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
			self.client.close()
			DomoticzEx.Debug(self.tracker_ip + ' ====> SSH client closed')
		except:
			DomoticzEx.Debug(self.tracker_ip + ' ====> Unable to close SSH session')
		if self.my_transport is None:
			DomoticzEx.Debug(self.tracker_ip + ' ====> SSH no transport')
		else:
			DomoticzEx.Debug(self.tracker_ip + ' ====> SSH wait for transport to close')
			self.my_transport.join()
		super().stop_now()
