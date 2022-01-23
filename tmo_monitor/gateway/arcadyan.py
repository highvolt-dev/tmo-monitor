import requests
import sys
import logging
from .base import ControllerBase

class CubeController(ControllerBase):
  def __init__(self):
    self.info_web = None
  # functions using authenticated app API endpoints
  def login_app(self):
    raise Exception('Not implemented')
  def get_site_info(self):
    raise Exception('Not implemented')
  # functions using authenticated web API endpoints
  def login_web(self):
    raise Exception('Not implemented')
  def reboot(self):
    raise Exception('Not implemented')
  # functions using unauthenticated API endpoints
  def get_all_info_web(self):
    if self.info_web is not None:
      return self.info_web
    try:
      signal_request = requests.get('http://192.168.12.1/TMI/v1/gateway?get=all')
    except:
      logging.critical("Could not query signal status, exiting.")
      sys.exit(2)
    signal_request.raise_for_status()
    self.info_web = signal_request.json()
    return self.info_web
  def get_uptime(self):
    return self.get_all_info_web()['time']['upTime']
  def get_signal_info(self):
    info = self.get_all_info_web()
    lte_info = info['signal']['4g']['bands']
    nr_info = info['signal']['5g']['bands']

    return {
      '4G': None if len(lte_info) == 0 else lte_info[0].upper(),
      '5G': None if len(nr_info) == 0 else nr_info[0]
    }