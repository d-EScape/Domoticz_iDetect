import Domoticz
import subprocess
import helpers.data_helper as data_helper
from trackers.tracker_base import tracker
import helpers.data_helper as data_helper
from datetime import datetime, timedelta
from time import sleep
try:
	import paramiko
	NOPARAMIKO = False
except ImportError:
	NOPARAMIKO = True

class ssh_tracker(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.trackerscript = ''
		self.sshbin = 'ssh'
		self.connected = False
		self.my_transport = None
		Domoticz.Debug(self.tracker_ip + ' Tracker is of the ssh kind')
		if NOPARAMIKO:
			Domoticz.Error('Missing paramiko module required for ssh. Install it using: sudo pip3 install paramiko')
		else:
			self.client = paramiko.SSHClient()
			self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	def poll_present_tag_ids(self):
		Domoticz.Debug(self.tracker_ip + ' Start poll and return results to ' + str(self.receiver_callback))
		success, raw_data = self.getfromssh(self.trackerscript)
		if not success:
			self.error_count = self.error_count + 1
			Domoticz.Log(self.tracker_ip + ' Could not be polled')
			return
		else:
			self.error_count = 0
			self.receiver_callback(raw_data)

	def prepare_for_polling(self):
		#Should be implemented in specfic tracker
		Domoticz.Debug(self.tracker_ip + ' Has no prepare_for_pollling method.')
		return True

	def ssh_connect(self):
		if NOPARAMIKO:
			Domoticz.Error('Missing paramiko module requred for ssh. Install it using: sudo pip3 install paramiko')
			return
		Domoticz.Debug(self.tracker_ip + ' ====> SSH start connect')
		if self.tracker_password == '':
			if self.tracker_keyfile != '':
				my_key_file = self.tracker_keyfile
				rsa_key = None
				try:
					rsa_key=paramiko.RSAKey.from_private_key_file(my_key_file)
				except Exception as e:
					Domoticz.Error(self.tracker_ip + ' ====> SSH Could not get RSA from private key. Exception: ' + str(e))
				Domoticz.Debug(self.tracker_ip + ' ====> SSH using key: ' + str(my_key_file))
				try:
					self.client.connect(self.tracker_ip, username=self.tracker_user, pkey=rsa_key, timeout=5)
				except Exception as e:
					Domoticz.Error(self.tracker_ip + ' SSH Could not connect (using custom key file). Exception: ' + str(e))
					self.connected = False
					return
			else:
				try:
					self.client.connect(self.tracker_ip, username=self.tracker_user, timeout=5)
				except Exception as e:
					Domoticz.Error(self.tracker_ip + ' SSH Could not connect (with os key). Exception: ' + str(e))
					self.connected = False
					return False
		else:
			try:
				self.client.connect(self.tracker_ip, username=self.tracker_user, password=self.tracker_password, timeout=5)
			except Exception as e:
				Domoticz.Error(self.tracker_ip + ' ====> SSH Could not connect (using password). Exception: ' + str(e))
				self.connected = False
				return False
		try:
			self.my_transport = self.client.get_transport()
			Domoticz.Status(self.tracker_ip + ' ====> SSH connection established')
		except:
			Domoticz.Error(self.tracker_ip + ' ====> SSH connection failed (no transport)')
			self.connected = False
			return False
		self.connected = True
		return True

	def getfromssh(self, tracker_cli, alltimeout=5, sshtimeout=3):
		if NOPARAMIKO:
			return False, ''
		Domoticz.Debug(self.tracker_ip + " ====> SSH Fetching data using: " + tracker_cli)
		starttime=datetime.now()
		if not self.connected:
			Domoticz.Debug(self.tracker_ip + ' ====> SSH not connected ... connecting')
			self.ssh_connect()
		if not self.connected:
			return False, ''
		try:
			stdin, stdout, stderr = self.client.exec_command(tracker_cli, timeout=5)
			ssh_output = stdout.read().decode("utf-8")
			ssh_error = stderr.read().decode("utf-8")
			if ssh_error != '':
				Domoticz.Error(self.tracker_ip + ' ====> SSH returned error:' + ssh_error)
			if ssh_output == '':
				Domoticz.Error(self.tracker_ip + ' ====> SSH returned empty response. Transport active: ' + str(self.my_transport.is_active()))
			Domoticz.Debug(self.tracker_ip + ' ====> SSH returned (decoded):' + ssh_output)
		except Exception as e:
			Domoticz.Error(self.tracker_ip + ' ====> SSH failed with exception: ' + str(e))
			try:
				self.client.close()
				Domoticz.Status(self.tracker_ip + ' ====> SSH resetting connection')
			except:
				Domoticz.Debug(self.tracker_ip + ' ====> SSH connection reset failed')
			self.connected = False
			return False, ''
		timespend=datetime.now()-starttime
		Domoticz.Debug(self.tracker_ip + " ====> SSH session took " + str(timespend.microseconds//1000) + " milliseconds.")
		return True, ssh_output

	def stop_now(self):
		self.is_ready = False
		try:
			self.client.close()
			Domoticz.Debug(self.tracker_ip + ' ====> SSH client closed')
		except:
			Domoticz.Debug(self.tracker_ip + ' ====> Unable to close SSH session')
		if self.my_transport is None:
			Domoticz.Debug(self.tracker_ip + ' ====> SSH no transport')
		else:
			Domoticz.Debug(self.tracker_ip + ' ====> SSH wait for transport to close')
			self.my_transport.join()
		super().stop_now()
