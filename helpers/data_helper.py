import re
from datetime import datetime

PATTERN_MAC = r'[a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}'
PATTERN_IP = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
CONFIG_DELIMITERS = ['@', ':', '=', '#']
OPTION_DELIMITER = '&'

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
	
def mac_from_data(raw_data):
	match_this = re.compile(PATTERN_MAC)
	found_this = match_this.findall(raw_data)
	return found_this
	
def ip_from_data(raw_data):
	match_this = re.compile(PATTERN_IP)
	found_this = match_this.findall(raw_data)
	return found_this

def clean_tag_id_list(raw_data, tag_type):
	if isinstance(raw_data, list):
		clean_list = [x.upper() for x in raw_data]
		return clean_list
	raw_data = raw_data.upper()
	if tag_type == 'mac_address':
		match_this = re.compile(PATTERN_MAC)
	elif tag_type == 'ip_address':
		match_this = re.compile(PATTERN_IP)
	else:
		Domoticz.Error('Undefined tag_type for data: ' + raw_data)
	clean_list = match_this.findall(raw_data)
	return clean_list
	
def guess_type(input):
	if isinstance(input, str):
		val = None
		try:
			val = int(input)
		except:
			if input.lower() == 'true':
				val = True
			elif input.lower() == 'false':
				val = False
		if val == None:
			val = input
		return val
	else:
		return input

def custom_or_default(config, field, default):
	field = field.lower()
	if field in config:
		if config[field] != '' and not config[field] is None:
			return config[field]
	return default
	
def get_config_part(config_str='', after='', before='', mandatory=False, default=None):
	if config_str == '':
		return None
	config_str = config_str.strip()
	if after != '':
		if after in config_str or mandatory:
			split_after = config_str.split(after, 1)[-1]
			for d in CONFIG_DELIMITERS:
				split_after = split_after.split(d, 1)[0]
			config_str = split_after.strip()
		else:
			config_str = ''
	if before != '':
		if before in config_str:
			split_before = config_str.split(before, 1)[0]
			for d in CONFIG_DELIMITERS:
				split_before = split_before.split(d, 1)[-1]
			config_str = split_before.strip()
		else:
			config_str = ''
	if config_str != '' and not config_str is None :
		return guess_type(config_str)
	return default
	
def options_from_string(input):
	if input is None or input.strip() == '':
		return {}
	illegal = 0
	seperate = input.strip().split('&')
	option_dict = {}
	for item in seperate:
		try:
			option, value_str = item.split('=', 1)
		except:
			illegal = illegal + 1 
			break
		option=option.lower()
		option_dict[option]=guess_type(value_str)
	if illegal > 0:
		option_dict['configuration errors']=illegal
	return option_dict
		
				
			

	