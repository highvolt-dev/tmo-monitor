#!/usr/bin/env python3
# Start by getting signal metrics
import sys
import requests
import subprocess
import hashlib
from base64 import b64encode
import secrets
import argparse
import platform
import getpass

class TrashCanController:
  def __init__(self, username, password):
    self.username = username
    self.password = password
    self.nonce = None
    self.csrf_token = None
    self.app_jar = None
    self.web_jar = None


  # functions using authenticated app API endpoints
  def login_app(self):
    login_request = requests.post('http://192.168.12.1/login_app.cgi', data={'name': self.username, 'pswd': self.password})
    login_request.raise_for_status()

    self.app_jar = requests.cookies.RequestsCookieJar()
    self.app_jar.set('sid', login_request.cookies['sid'], domain='192.168.12.1', path='/')
    self.app_jar.set('lsid', login_request.cookies['lsid'], domain='192.168.12.1', path='/')

  def get_site_info(self):
    if not self.app_jar:
      self.login_app()
    stat_request = requests.get('http://192.168.12.1/cell_status_app.cgi', cookies=self.app_jar)
    stat_request.raise_for_status()
    meta = stat_request.json()['cell_stat_lte'][0]

    return {
      'eNBID': int(meta['eNBID']),
      'PLMN': meta['MCC'] + '-' + meta['MNC']
    }

  # functions using authenticated web API endpoints
  def login_web(self):
    nonce_request = requests.get('http://192.168.12.1/login_web_app.cgi?nonce')
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

    login_request = requests.post('http://192.168.12.1/login_web_app.cgi', data=login_request_body)
    login_request.raise_for_status()
    self.web_jar = requests.cookies.RequestsCookieJar()
    self.web_jar.set('sid', login_request.cookies['sid'], domain='192.168.12.1', path='/')
    self.web_jar.set('lsid', login_request.cookies['lsid'], domain='192.168.12.1', path='/')
    login_response = login_request.json()
    self.csrf_token = login_response['token']

  def reboot(self):
    if not (self.csrf_token or self.web_jar):
      self.login_web()
    reboot_request = requests.post('http://192.168.12.1/reboot_web_app.cgi', data={'csrf_token': self.csrf_token}, cookies=self.web_jar)
    reboot_request.raise_for_status()


  # functions using unauthenticated API endpoints
  def get_uptime(self):
    uptime_req = requests.get('http://192.168.12.1/dashboard_device_info_status_web_app.cgi')
    uptime_req.raise_for_status()
    return uptime_req.json()['device_app_status'][0]['UpTime']
  
  def get_signal_info(self):
    signal_request = requests.get('http://192.168.12.1/fastmile_radio_status_web_app.cgi')
    signal_request.raise_for_status()
    return signal_request.json()


  # functions that don't touch the API
  def ping(self, ping_host, interface = None):
    is_win = platform.system() == 'Windows'
    ping_cmd = ['ping']
    if interface:
      ping_cmd.append('-S' if is_win else '-I')
      ping_cmd.append(interface)
    ping_cmd.append('-n' if is_win else '-c')
    ping_cmd.append('1')
    ping_cmd.append(ping_host)
    ping_exec = subprocess.run(ping_cmd, capture_output=True)
    print(ping_exec.stdout.decode('utf-8'))
    if is_win and 'Destination host unreachable' in str(ping_exec.stdout):
      return False
    else:
      return ping_exec.returncode == 0


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


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Check T-Mobile Home Internet cellular band(s) and connectivity and reboot if necessary')
  parser.add_argument('username', type=str, help='the username (most likely "admin")')
  parser.add_argument('password', type=str, help='the administrative password (will be requested at runtime if not passed as argument)', nargs='?')
  parser.add_argument('-I', '--interface', type=str, help='the network interface to use for ping. pass the source IP on Windows')
  parser.add_argument('-H', '--ping-host', type=str, default='google.com', help='the host to ping (defaults to google.com)')
  parser.add_argument('-R', '--reboot', action='store_true', help='skip health checks and immediately reboot gateway')
  parser.add_argument('-r', '--skip-reboot', action='store_true', help='skip rebooting gateway')
  parser.add_argument('--skip-bands', action='store_true', help='skip check for connected band')
  parser.add_argument('--skip-5g-bands', action='store_true', help='skip check for connected 5g band')
  parser.add_argument('--skip-ping', action='store_true', help='skip check for successful ping')
  parser.add_argument('-4', '--4g-band', type=str, action='append', dest='primary_band', default=None, choices=['B2', 'B4', 'B5', 'B12', 'B13', 'B25', 'B26', 'B41', 'B46', 'B48', 'B66', 'B71'], help='the 4g band(s) to check')
  parser.add_argument('-5', '--5g-band', type=str, action='append', dest='secondary_band', default=None, choices=['n41', 'n71'], help='the 5g band(s) to check (defaults to n41)')
  parser.add_argument('--uptime', type=int, default=90, help='how long the gateway must be up before considering a reboot (defaults to 90 seconds)')
  parser.add_argument('--enbid', type=int, default=None, help='check for a connection to a given eNB ID')
  args = parser.parse_args()

  if args.skip_reboot and args.reboot:
    print('Incompatible options: --reboot and --skip-reboot\n', file=sys.stderr)
    parser.print_help(sys.stderr)
    sys.exit(2)

  if not args.secondary_band:
    args.secondary_band = ['n41']

  if not args.password:
    args.password = getpass.getpass('Password: ')

  tc_control = TrashCanController(args.username, args.password)

  reboot_requested = args.reboot

  if args.enbid and not reboot_requested:
    site_meta = tc_control.get_site_info()
    if site_meta['eNBID'] != args.enbid:
      print('Not on eNB ID ' + str(args.enbid) + '.' + (' Reboot requested.' if not args.skip_reboot else ''))
      reboot_requested = True
    else:
      print('eNB ID check passed.')

  if not args.skip_bands and not reboot_requested:
    signal_info = tc_control.get_signal_info()

    if args.primary_band:
      band_4g = signal_info['cell_LTE_stats_cfg'][0]['stat']['Band']
      if band_4g not in args.primary_band:
        print('Not on ' + ('one of ' if len(args.primary_band) > 1 else '') + ', '.join(args.primary_band) + '.' + (' Reboot requested.' if not args.skip_reboot else ''))
        reboot_requested = True
      else:
        print('Camping on ' + band_4g + '.' + (' Not rebooting.' if not args.skip_reboot else ''))

    if not args.skip_5g_bands:
      band_5g = signal_info['cell_5G_stats_cfg'][0]['stat']['Band']
      if band_5g not in args.secondary_band:
        print('Not on ' + ('one of ' if len(args.secondary_band) > 1 else '') + ', '.join(args.secondary_band) + '.' + (' Reboot requested.' if not args.skip_reboot else ''))
        reboot_requested = True
      else:
        print('Camping on ' + band_5g + '.' + (' Not rebooting.' if not args.skip_reboot else ''))


  if not args.skip_ping and not reboot_requested and not tc_control.ping(args.ping_host, args.interface):
    print('Could not ping ' + args.ping_host + '.' + (' Reboot requested.' if not args.skip_reboot else ''))
    reboot_requested = True

  if args.skip_reboot and reboot_requested:
    print('Skipping reboot.')
  elif reboot_requested:
    if args.reboot or tc_control.get_uptime() >= args.uptime:
      print('Rebooting.')
      tc_control.reboot()
    else:
      print('Uptime threshold not met for reboot.')
  else:
    print('No reboot necessary.')
