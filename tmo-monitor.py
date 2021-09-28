#!/usr/bin/env python
# Start by getting signal metrics
import os
import requests
import subprocess
import hashlib
from base64 import b64encode
import secrets
import argparse
import getpass
import json

class TMobileGatewayInterface:
  def __init__(self, user_hash = None, random_key_hash = None, response = None, nonce = None, creds_filename = None):
    if creds_filename:
      self.load_credentials(creds_filename)
    else:
      self.user_hash = user_hash
      self.random_key_hash = random_key_hash
      self.response = response
      self.nonce = nonce
    self.jar = requests.cookies.RequestsCookieJar()
    self.csrf_token = None

  def fetch_credentials(self, username, password):
    nonce_request = requests.get('http://192.168.12.1/login_web_app.cgi?nonce')
    nonce_request.raise_for_status()
    nonce_response = nonce_request.json()
    
    user_pass_sha = self.sha256(username, password)
    self.user_hash = self.sha256url(username, nonce_response['nonce'])
    self.random_key_hash = self.sha256url(nonce_response['randomKey'], nonce_response['nonce'])
    self.response = self.sha256url(user_pass_sha, nonce_response['nonce'])
    self.nonce = self.base64url_escape(nonce_response['nonce'])
  
  def save_credentials(self, filename):
    creds_json = {
      'user_hash': self.user_hash,
      'random_key_hash': self.random_key_hash,
      'response': self.response,
      'nonce': self.nonce
    }
    with open(filename, 'w') as file:
      json.dump(creds_json, file)
    print('Credentials saved to ' + filename)
  
  def load_credentials(self, filename):
    with open(filename, 'r') as file:
      creds_json = json.load(file)
    self.user_hash = creds_json['user_hash']
    self.random_key_hash = creds_json['random_key_hash']
    self.response = creds_json['response']
    self.nonce = creds_json['nonce']
    print('Credentials loaded from ' + filename)

  def login(self):
    base_key = b64encode(secrets.token_bytes(16)).decode('utf-8')
    base_iv = b64encode(secrets.token_bytes(16)).decode('utf-8')
    login_request_body = {
      'userhash': self.user_hash,
      'RandomKeyhash': self.random_key_hash,
      'response': self.response,
      'nonce': self.nonce,
      'enckey': self.base64url_escape(base_key),
      'enciv': self.base64url_escape(base_iv)
    }
  
    login_request = requests.post('http://192.168.12.1/login_web_app.cgi', data=login_request_body)
    login_request.raise_for_status()
    login_response = login_request.json()

    self.jar.set('sid', login_request.cookies['sid'], domain='192.168.12.1', path='/')
    self.jar.set('lsid', login_request.cookies['lsid'], domain='192.168.12.1', path='/')
    self.csrf_token = login_response['token']

  def reboot(self):
    if not self.csrf_token:
      self.logn()
    reboot_request = requests.post('http://192.168.12.1/reboot_web_app.cgi', data={'csrf_token': self.csrf_token}, cookies=self.jar)
    reboot_request.raise_for_status()
  
  def check_status(self, interface = None, ping_host = 'google.com'):
    # returns True if status is OK, False if reboot needed
    signal_request = requests.get('http://192.168.12.1/fastmile_radio_status_web_app.cgi')
    signal_request.raise_for_status()
    signal_info = signal_request.json()
    band_5g = signal_info['cell_5G_stats_cfg'][0]['stat']['Band']
    if band_5g != 'n41':
      print('Not on n41. Reboot requested.')
      return False
    else:
      print('Camping on n41.')
      ping_cmd = ['ping']
      if interface:
        ping_cmd.append('-I')
        ping_cmd.append(interface)
      ping_cmd.append('-c')
      ping_cmd.append('1')
      ping_cmd.append(ping_host)
      if subprocess.call(ping_cmd) != 0:
        print('Could not ping ' + ping_host + '. Reboot requested.')
        return False
      else:
        print('Successfully pinged ' + ping_host + '.')
        return True

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


parser = argparse.ArgumentParser(description='Check T-Mobile Home Internet 5g band and connectivity and reboot if necessary')
parser.add_argument('-u', '--username', type=str, help='the administrative username (defaults to "admin")', default='admin')
parser.add_argument('-p', '--password', type=str, help='the administrative password (will be prompted if not passed as argument)')
parser.add_argument('-I', '--interface', type=str, help='the network interface to use for ping')
parser.add_argument('-H', '--ping-host', type=str, default='google.com', help='the host to ping (defaults to google.com)')
parser.add_argument('-g', '--generate-credentials', action='store_true', help='generate credentials and exit (saved as credentials.json unless used in combination with -f)')
parser.add_argument('-f', '--credentials-file', type=str, help='file from which to save/load saved credentials')
parser.add_argument('-R', '--reboot', action='store_true', help='skip health checks and immediately reboot gateway')
args = parser.parse_args()

if args.credentials_file and not args.generate_credentials:
  gateway = TMobileGatewayInterface(creds_filename = args.credentials_file)
else:
  if not args.password:
    args.password = getpass.getpass()
  gateway = TMobileGatewayInterface()
  gateway.fetch_credentials(args.username, args.password)

if args.generate_credentials:
  args.credentials_file = args.credentials_file or 'credentials.json'
  gateway.save_credentials(args.credentials_file)
  exit()

reboot_requested = args.reboot

if not reboot_requested:
  reboot_requested = not gateway.check_status(args.interface, args.ping_host)

if reboot_requested:
  print('Rebooting.')
  gateway.login()
  gateway.reboot()
else:
  print('No reboot necessary.')
