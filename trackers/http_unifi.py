# Tracker for Ubiquiti Unifi Controller

import DomoticzEx
import requests
import json
from trackers.tracker_base import tracker


class http_unifi(tracker):
	def __init__(self, *args, **kwargs):
		# Update default port
		if self.tracker_port is None:
			self.tracker_port = 443

		super().__init__(*args, **kwargs)

		self.baseurl = 'https://{}:{}'.format(self.tracker_ip, self.tracker_port)
		self.site = 'default'
		self.verify_ssl = False
		self.prepare_for_polling()

	def poll_present_tag_ids(self):
		try:
			if not self.http_session:
				self.connect()

			response = self.http_session.get(
				"{}/api/s/{}/stat/sta".format(self.baseurl, self.site),
				verify=self.verify_ssl, 
				data="json={}"
			)
		except Exception as e:
			DomoticzEx.Error(self.tracker_ip + ' Polling error: ' + str(e))
			self.close_connection()

		if (response.status_code == 401):
			self.close_connection()
			DomoticzEx.Error(self.tracker_ip + ' Invalid login, or login has expired')
			return

		raw_data = response.text
		DomoticzEx.Debug(self.tracker_ip + ' Returned: ' + raw_data)

		self.receiver_callback(raw_data)

	def connect(self):
		login_data = {
			'username': self.tracker_user,
			'password': self.tracker_password
		}

		self.http_session = requests.Session()

		response = self.http_session.post(
			"{}/api/login".format(self.baseurl),
			data=json.dumps(login_data),
			verify=self.verify_ssl
		)

		if response.status_code == 400:
			DomoticzEx.Error(self.tracker_ip + 'Failed to log in to Unifi API')
			return False

		DomoticzEx.Status(self.baseurl + ' Initialized as Ubiquiti Unifi Controller API')
		return True

	def disconnect(self):
		try:
			self.http_session.get("{}/logout".format(self.baseurl))
		finally:
			self.close_connection()

	def close_connection(self):
		try:
			self.http_session.close()
			self.http_session = None
			DomoticzEx.Debug(self.tracker_ip + ' HTTP session closed')
		except Exception as e:
			DomoticzEx.Debug(self.tracker_ip + ' Close session exception: ' + str(e))
		return
	   
	def prepare_for_polling(self):
		if self.connect():
			self.is_ready = True

	def stop_now(self):
		self.is_ready = False
		self.disconnect()

		super().stop_now()
