import re
from datetime import datetime

PATTERN_MAC = r'[a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}'
PATTERN_IP = r'[a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}' #need pattern for ip

# def is_mac_address(input):
# 	match_this = re.compile(PATTERN_MAC)
# 	result = match_this.match(input)
# 	if result not is None:
# 		return True
# 	else:
# 		return False
	
def is_mac_address(input):
	segments = input.split(":")
	if len(segments) != 6:
		return False
	for s in segments:
		if len(s) != 2:
			return False
		try:
			val = int(s, 16)
		except:
			return False
		if not (0 <= val <= 255):
			return False
	return True

def is_ip_address(input):
	segments = input.split(".")
	if len(segments) != 4:
		return False
	for s in segments:
		try:
			val = int(s)
		except:
			return False
		if not (0 <= val <= 255):
			return False
	return True

def time_since_last(past_moment):
	number_of_seconds = (datetime.now() - past_moment).total_seconds()
	return number_of_seconds

def clean_tag_id_list(raw_data, tag_type):
	if isinstance(raw_data, list):
		clean_list = [x.upper() for x in raw_data]
		return clean_list
	if isinstance(raw_data, bytes):
		str_data = raw_data.decode("utf-8").upper()
	elif isinstance(raw_data, str):
		str_data = raw_data.upper()
	if tag_type == 'mac_address':
		match_this = re.compile(PATTERN_MAC)
	elif tag_type == 'ip_address':
		match_this = re.compile(PATTERN_IP)
	else:
		Domoticz.Error('Undefined tag_type for data: ' + str_data)
	clean_list = match_this.findall(str_data)
	return clean_list
	

	