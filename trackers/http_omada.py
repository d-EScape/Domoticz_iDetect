# Tracker for  TP-link Omada Controller
# Omada code nicked from https://github.com/titilambert/tplink

import Domoticz
import requests
import json
from trackers.tracker_base import tracker
from urllib.parse import urlparse
import socket

class http_omada(tracker):
    def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
        # Update default port
        if tracker_port == 22:
            tracker_port = 8443

        super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
        self.baseurl = 'https://{}:{}'.format(self.tracker_ip, self.tracker_port)
        self.site = 'default'
        self.verify_ssl = False
        self.token = ''
        self.prepare_for_polling()

    def poll_present_tag_ids(self):
        if not self.session:
            self.connect()
        current_page_size = 10
        current_page = 1
        clients_path = "/web/v1/controller?userStore&token="
        total_rows = current_page_size + 1
        mac_string = ''
        while (current_page - 1) * current_page_size <= total_rows:
            clients_data = {"method": "getGridActiveClients",
                            "params": {"sortOrder": "asc",
                                      "currentPage": current_page,
                                      "currentPageSize": current_page_size,
                                      "filters": {"type": "all"}
                                      }
                           }
            res = self.session.post(self.baseurl + clients_path + self.token,
                               data=json.dumps(clients_data),
                               verify=self.verify_ssl)
            # Domoticz.Debug(self.tracker_ip + ' URL: ' + self.baseurl + clients_path + self.token)
            # Domoticz.Debug(self.tracker_ip + ' Returned: ' + res.text)
            results = res.json()['result']
            total_rows = results['totalRows']
            for data in results['data']:
                mac_string = mac_string + data['mac'].replace('-', ':') + ','
            current_page += 1

        Domoticz.Debug(self.tracker_ip + ' Returned: ' + mac_string)
        self.receiver_callback(mac_string)

    def connect(self):
        login_path = "/api/user/login?ajax"

        self.session = requests.Session()
        login_data = {"method": "login",
                      "params": {"name": self.tracker_user,
                                 "password": self.tracker_password
                                }
                     }
        res = self.session.post(self.baseurl + login_path,
                           data=json.dumps(login_data),
                           verify=self.verify_ssl)
        # Domoticz.Debug(self.tracker_ip + ': ' +  res.text)
        if res.json().get('msg') != 'Log in successfully.':
            Domoticz.Error(self.tracker_ip + 'Failed to log in to Omada API')
            return False
        # Get token
        self.token = res.json()['result']['token']
        Domoticz.Status(self.baseurl + ' Initialized as TP-link Omada Controller API')
        return True

    def disconnect(self):
        self.close_connection()

    def close_connection(self):
        try:
            self.session.close()
            self.session = None
            Domoticz.Debug(self.tracker_ip + ' HTTP session closed')
        except Exception as e:
            Domoticz.Debug(self.tracker_ip + ' Close session exception: ' + str(e))
        return
       
    def prepare_for_polling(self):
        if self.connect():
            self.is_ready = True

    def stop_now(self):
        self.is_ready = False
        self.disconnect()

        super().stop_now()
