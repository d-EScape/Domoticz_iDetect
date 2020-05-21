import Domoticz
from trackers.ssh_tracker import ssh_tracker
import helpers.tracker_cli_helper as tracker_cli_helper
import helpers.data_helper as data_helper
import re
from datetime import datetime

ARP_PATTERN_MAC = r'(?=.*\bDC\b|.*\b C\b)(?:\S+ ){3}(\S+)'
ARP_PATTERN_IP = r'(?=.*\bDC\b|.*\b C\b)(?:\S+ ){2}(\S+)'

def remove_white_space(data):
	this_data = re.sub(' +', ' ',data)
	return this_data

def clean_tag_id_list_arp(raw_data, tag_type):
	if isinstance(raw_data, list):
		raw_list = raw_data
	else:
		raw_data = remove_white_space(raw_data)
		raw_data = raw_data.upper()
		if tag_type == 'mac_address':
			match_this = re.compile(ARP_PATTERN_MAC)
		elif tag_type == 'ip_address':
			match_this = re.compile(ARP_PATTERN_IP)
		else:
			Domoticz.Error('Undefined tag_type for data: ' + raw_data)
			return []
		raw_list = match_this.findall(raw_data)
	clean_list = [data_helper.clean_tag(x) for x in raw_list]
	return clean_list

class ssh_routeros_arp(ssh_tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.prepare_for_polling()

	def prepare_for_polling(self):
		Domoticz.Debug('routeros-arp prepare_for_polling')
		self.trackerscript = "ip arp print"
		self.is_ready = True

	def receiver_callback(self, raw_data):
		Domoticz.Debug('routeros-arp receiver_callback called')
		#Domoticz.Debug(raw_data + ' raw_data')
		#Domoticz.Debug(self.tag_type + ' self.tag_type')
		self.found_tag_ids = clean_tag_id_list_arp(raw_data, self.tag_type)
		if not self.interpreter_callback is None:
			self.interpreter_callback(self)
		else:
			Domoticz.Debug(self.tracker_ip + ' No interpreter_callback registered. Ignoring new data.')

