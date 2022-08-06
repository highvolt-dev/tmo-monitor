import requests
import sys
import logging
import math
from .base import ControllerBase
from ..status import ExitStatus

class CubeController(ControllerBase):
  def __init__(self, username, password):
    self.username = username
    self.password = password
    self.info_web = None
    self.app_token = None
  # functions using authenticated app API endpoints
  def login_app(self):
    try:
      login_request = requests.post('http://192.168.12.1/TMI/v1/auth/login', json={'username': self.username, 'password': self.password})
    except:
      logging.critical("Could not post login request, exiting.")
      sys.exit(ExitStatus.API_ERROR.value)
    login_request.raise_for_status()
    self.app_token = login_request.json()['auth']['token']

  def get_site_info(self):
    try:
      if not self.app_token:
        self.login_app()
      stat_request = requests.get('http://192.168.12.1/TMI/v1/network/telemetry?get=all', headers={'Authorization': 'Bearer ' + self.app_token})
    except:
      logging.critical("Could not query site info, exiting.")
      sys.exit(ExitStatus.API_ERROR.value)

    stat_request.raise_for_status()
    meta = stat_request.json()['cell']['4g']

    return {
      'eNBID': math.floor(int(meta['ecgi'][6:])/256),
      'PLMN': meta['mcc'] + '-' + meta['mnc']
    }
  def reboot(self):
    try:
      if not self.app_token:
        self.login_app()
      reboot_request = requests.post('http://192.168.12.1/TMI/v1/gateway/reset?set=reboot', headers={'Authorization': 'Bearer ' + self.app_token})
    except:
      logging.critical("Could not post reboot request, exiting.")
      sys.exit(ExitStatus.API_ERROR.value)
    reboot_request.raise_for_status()
  # functions using authenticated web API endpoints
  def login_web(self):
    raise Exception('Not implemented')
  # functions using unauthenticated API endpoints
  def get_all_info_web(self):
    if self.info_web is not None:
      return self.info_web
    try:
      signal_request = requests.get('http://192.168.12.1/TMI/v1/gateway?get=all')
    except:
      logging.critical("Could not query signal status, exiting.")
      sys.exit(ExitStatus.API_ERROR.value)
    signal_request.raise_for_status()
    self.info_web = signal_request.json()
    return self.info_web
  def get_uptime(self):
    return self.get_all_info_web()['time']['upTime']
  def get_signal_info(self):
    info = self.get_all_info_web()
    lte_info = info['signal']['4g']['bands']
    if '5g' in info['signal']:
      nr_info = info['signal']['5g']['bands']
    else:
      nr_info = []

    return {
      '4G': None if len(lte_info) == 0 else lte_info[0].upper(),
      '5G': None if len(nr_info) == 0 else nr_info[0]
    }