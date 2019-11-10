import re
from datetime import datetime

def time_since_last(past_moment):
	number_of_seconds = (datetime.now() - past_moment).total_seconds()
	return number_of_seconds

def clean_mac_list(raw_data):
	if isinstance(raw_data, list):
		clean_list = [x.upper() for x in raw_data]
		return clean_list
	if isinstance(raw_data, bytes):
		str_data = raw_data.decode("utf-8").upper()
	elif isinstance(raw_data, str):
		str_data = raw_data.upper()
	match_this = re.compile(r'[a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}[:][a-fA-F0-9]{2}')
	clean_list = match_this.findall(str_data)
	return clean_list
	

	