from .base import ControllerBase
from base64 import b64encode
import hashlib
import logging
import requests
import secrets
import sys

class TrashCanController(ControllerBase):
  def __init__(self, username, password):
    self.username = username
    self.password = password
    self.nonce = None
    self.csrf_token = None
    self.app_jar = None
    self.web_jar = None

  # functions using authenticated app API endpoints
  def login_app(self):
    try:
      login_request = requests.post('http://192.168.12.1/login_app.cgi', data={'name': self.username, 'pswd': self.password})
    except:
      logging.critical("Could not post login request, exiting.")
      sys.exit(2)
    login_request.raise_for_status()

    self.app_jar = requests.cookies.RequestsCookieJar()
    self.app_jar.set('sid', login_request.cookies['sid'], domain='192.168.12.1', path='/')
    self.app_jar.set('lsid', login_request.cookies['lsid'], domain='192.168.12.1', path='/')

  def get_site_info(self):
    try:
      if not self.app_jar:
        self.login_app()
      stat_request = requests.get('http://192.168.12.1/cell_status_app.cgi', cookies=self.app_jar)
    except:
      logging.critical("Could not query site info, exiting.")
      sys.exit(2)

    stat_request.raise_for_status()
    meta = stat_request.json()['cell_stat_lte'][0]

    return {
      'eNBID': int(meta['eNBID']),
      'PLMN': meta['MCC'] + '-' + meta['MNC']
    }

  # functions using authenticated web API endpoints
  def login_web(self):
    try:
      nonce_request = requests.get('http://192.168.12.1/login_web_app.cgi?nonce')
    except:
      logging.critical("Could not query nonce, exiting.")
      sys.exit(2)

    nonce_request.raise_for_status()
    nonce_response = nonce_request.json()
    self.nonce = nonce_response['nonce']

    user_pass_hash = self.sha256(self.username, self.password)
    user_pass_nonce_hash = self.sha256url(user_pass_hash, self.nonce)
    login_request_body = {
      'userhash': self.sha256url(self.username, self.nonce),
      'RandomKeyhash': self.sha256url(nonce_response['randomKey'], self.nonce),
      'response': user_pass_nonce_hash,
      'nonce': self.base64url_escape(self.nonce),
      'enckey': self.base64url_escape(b64encode(secrets.token_bytes(16)).decode('utf-8')),
      'enciv': self.base64url_escape(b64encode(secrets.token_bytes(16)).decode('utf-8'))
    }

    try:
      login_request = requests.post('http://192.168.12.1/login_web_app.cgi', data=login_request_body)
    except:
      logging.critical("Could not post login request, exiting.")
      sys.exit(2)
    login_request.raise_for_status()
    self.web_jar = requests.cookies.RequestsCookieJar()
    self.web_jar.set('sid', login_request.cookies['sid'], domain='192.168.12.1', path='/')
    self.web_jar.set('lsid', login_request.cookies['lsid'], domain='192.168.12.1', path='/')
    login_response = login_request.json()
    self.csrf_token = login_response['token']

  def reboot(self):
    try:
      if not (self.csrf_token or self.web_jar):
        self.login_web()
      reboot_request = requests.post('http://192.168.12.1/reboot_web_app.cgi', data={'csrf_token': self.csrf_token}, cookies=self.web_jar)
    except:
      logging.critical("Could not post reboot request, exiting.")
      sys.exit(2)
    reboot_request.raise_for_status()

  # functions using unauthenticated API endpoints
  def get_uptime(self):
    try:
      uptime_req = requests.get('http://192.168.12.1/dashboard_device_info_status_web_app.cgi')
    except:
      logging.critical("Could not query modem uptime, exiting.")
      sys.exit(2)
    uptime_req.raise_for_status()
    return uptime_req.json()['device_app_status'][0]['UpTime']

  def get_signal_info(self):
    try:
      signal_request = requests.get('http://192.168.12.1/fastmile_radio_status_web_app.cgi')
    except:
      logging.critical("Could not query signal status, exiting.")
      sys.exit(2)
    signal_request.raise_for_status()
    info = signal_request.json()

    return {
      '4G': info['cell_LTE_stats_cfg'][0]['stat']['Band'],
      '5G': info['cell_5G_stats_cfg'][0]['stat']['Band']
    }

  # helper functions - maybe move these into their own class and import it later?
  def base64url_escape(self, b64):
    out = ''
    for c in b64:
      if c == '+':
        out += '-'
      elif c == '/':
        out += '_'
      elif c == '=':
        out += '.'
      else:
        out += c
    return out

  def sha256(self, val1, val2):
    hash = hashlib.sha256()
    hash.update((val1 + ':' + val2).encode())
    return b64encode(hash.digest()).decode('utf-8')

  def sha256url(self, val1, val2):
    return self.base64url_escape(self.sha256(val1, val2))