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
import time
import logging
import os
from dotenv import load_dotenv, find_dotenv
import re

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
    return signal_request.json()

  # functions that don't touch the API
  def ping(self, ping_host, ping_count, ping_interval, interface = None):
    is_win = platform.system() == 'Windows'
    ping_cmd = ['ping']
    if interface:
      ping_cmd.append('-S' if is_win else '-I')
      ping_cmd.append(interface)
    ping_cmd.append('-n' if is_win else '-c')
    ping_cmd.append('1')
    ping_cmd.append(ping_host)

    def ping_time(ping_index):
      if ping_index > 0:
        time.sleep(ping_interval)
      ping_exec = subprocess.run(ping_cmd, capture_output=True)
      print(ping_exec.stdout.decode('utf-8'))
      if ping_exec.returncode != 0:
        return -1
      pattern = b'[rtt|round-trip] min/avg/max/mdev = \d+.\d+/(\d+.\d+)/\d+.\d+/\d+.\d+ ms'
      if is_win:
        pattern = b'Minimum = \d+ms, Maximum = \d+ms, Average = (\d+)ms'
      ping_ms = re.search(pattern, ping_exec.stdout)
      return round(float(ping_ms.group(1)))

    for i in range (ping_count):
      result = ping_time(i)
      if result > 0:
        return result
    return -1

    #   if is_win and 'Destination host unreachable' in str(ping_exec.stdout):
    #     return False
    #   else:
    #     return ping_exec.returncode == 0
    # return any(is_ping_success(i) for i in range(ping_count))



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


class Configuration:
  def __init__(self):
    # Set default values
    self.reboot_now = False
    self.skip_reboot = False
    self.login = dict([('username', 'admin'), ('password', '')])
    self.ping = dict([('interface', ''), ('ping_host', 'google.com'), ('ping_count', 1), ('ping_interval', 10)])
    self.connection = dict([('primary_band', ''), ('secondary_band', 'n41'), ('enbid', ''), ('uptime', '')])
    self.reboot = dict([('uptime', 90), ('ping', False), ('4G_band', False), ('5G_band', False), ('enbid', False)])
    self.general = dict([('print_config', False), ('logfile', '')])
  
    # Command line arguments override defaults & .env file
    self.read_environment()
    args = self.parse_commandline()
    self.parse_arguments(args)

    if self.skip_reboot and self.reboot_now:
      msg = 'Incompatible options: --reboot and --skip-reboot\n'
      print(msg, file=sys.stderr)
      logging.error(msg)
      if sys.stdin and sys.stdin.isatty():
        self.parser.print_help(sys.stderr)
      sys.exit(2)
    if self.skip_reboot:
      for var in {'ping', '4G_band', '5G_band', 'enbid'}:
        self.reboot[var] = False
    if not self.login['password']:    
      self.password = getpass.getpass('Password: ')


  def read_environment(self):
    try:
      envfile=find_dotenv()
      load_dotenv(envfile)
    except:
      logging.debug("No .env file found")
      return
    for var in {'username', 'password'}:
      tmp = os.environ.get('tmo_' + var)
      if tmp != None:
        self.login[var] = tmp
    for var in {'interface', 'ping_host', 'ping_count', 'ping_interval'}:
      tmp = os.environ.get('tmo_' + var)
      if tmp != None:
        self.ping[var] = tmp  
    for var in {'primary_band', 'secondary_band'}:
      tmp = os.environ.get('tmo_' + var)
      if tmp != None:
        splits = tmp.split(',')
        self.connection[var] = splits
    tmp = os.environ.get('tmo_enbid')
    if tmp != None:
      self.connection['enbid'] = tmp
    for var in {'uptime', 'ping', '4G_band', '5G_band', 'enbid'}:
      tmp = os.environ.get('tmo_' + var + '_reboot')
      if tmp != None:
        if tmp.lower() == 'true':
          self.reboot[var] = True
        else:
          self.reboot[var] = False
    tmp = os.environ.get('tmo_skip_reboot')
    if tmp != None:
      if tmp.lower() == 'true':
        self.reboot[var] = True
      else:
        self.reboot[var] = False
    tmp = os.environ.get('tmo_print_config')
    if tmp != None:
        if tmp.lower() == 'true':
          self.general['print_config'] = True
        else:
          self.general['print_config'] = False
    tmp = os.environ.get('tmo_logfile')
    if tmp != None:
        self.general['logfile'] = tmp
    tmp = os.environ.get('tmo_log_all')
    if tmp != None:
        if tmp.lower() == 'true':
          self.general['log_all'] = True
        else:
          self.general['log_all'] = False

     
    
  def parse_commandline(self):
    self.parser = argparse.ArgumentParser(description='Check T-Mobile Home Internet cellular band(s) and connectivity and reboot if necessary')
    # login settings
    self.parser.add_argument('username', type=str, help='the username (most likely "admin")', nargs='?')
    self.parser.add_argument('password', type=str, help='the administrative password (will be requested at runtime if not passed as argument)', nargs='?')
    # ping configuration 
    self.parser.add_argument('-I', '--interface', type=str, help='the network interface to use for ping. pass the source IP on Windows')
    self.parser.add_argument('-H', '--ping-host', type=str, default='google.com', help='the host to ping (defaults to google.com)')
    self.parser.add_argument('--ping-count', type=int, default='1', help='how many ping health checks to perform')
    self.parser.add_argument('--ping-interval', type=int, default='10', help='how long in seconds to wait between ping health checks')
    # reboot settings
    self.parser.add_argument('-R', '--reboot', action='store_true', help='skip health checks and immediately reboot gateway')
    self.parser.add_argument('-r', '--skip-reboot', action='store_true', help='skip rebooting gateway')
    self.parser.add_argument('--skip-bands', action='store_true', help='skip check for connected band')
    self.parser.add_argument('--skip-5g-bands', action='store_true', help='skip check for connected 5g band')
    self.parser.add_argument('--skip-ping', action='store_true', help='skip check for successful ping')
    self.parser.add_argument('--skip-enbid', action='store_true', help='skip check for connected eNB ID')
    self.parser.add_argument('--uptime', type=int, default=90, help='how long the gateway must be up before considering a reboot (defaults to 90 seconds)')
    # connection configuration
    self.parser.add_argument('-4', '--4g-band', type=str, action='append', dest='primary_band', default=None, choices=['B2', 'B4', 'B5', 'B12', 'B13', 'B25', 'B26', 'B41', 'B46', 'B48', 'B66', 'B71'], help='the 4g band(s) to check')
    self.parser.add_argument('-5', '--5g-band', type=str, action='append', dest='secondary_band', default=None, choices=['n41', 'n71'], help='the 5g band(s) to check (defaults to n41)')
    self.parser.add_argument('--enbid', type=int, default=None, help='check for a connection to a given eNB ID')
    return self.parser.parse_args()

  def parse_arguments(self, args):
    for var in {'username', 'password'}:
      tmp = getattr(args, var)
      if tmp != None:
        self.login[var] = tmp
    for var in {'interface', 'ping_host', 'ping_count', 'ping_interval'}:
      tmp = getattr(args, var)
      if tmp != None:
        self.ping[var] = tmp  
    for var in {'primary_band', 'secondary_band', 'enbid'}:
      tmp = getattr(args, var)
      if tmp != None:
        self.connection[var] = tmp
    if args.uptime != None:
      self.reboot['uptime'] = args.uptime
    
    if args.skip_ping == True:
      self.reboot['ping'] = False
    if self.connection['primary_band'] == '' or args.skip_bands == True:
      self.reboot['4G_band'] = False
    if self.connection['secondary_band'] == '' or args.skip_5g_bands == True:
      self.reboot['5G_band'] = False
    if self.connection['enbid'] == '' or args.skip_enbid == True:
      self.reboot['enbid'] = False

    if args.skip_reboot == True:
      self.skip_reboot = True
    if args.reboot == True:
      self.reboot_now = True

  def print_config(self):
    print("Script configuration:")
    if sys.stdin and sys.stdin.isatty():
      print("  Login info:")
      print("    Username: " + self.login.get('username') if self.login.get('username') else '')
      print("    Password: " + self.login.get('password') if self.login.get('password') else '')
    print("  Ping configuration:")
    (print("    Interface: " + self.ping.get('interface')) if self.ping.get('interface') else '')
    (print("    Host: " + self.ping.get('ping_host')) if self.ping.get('ping_host') else '')
    (print("    Count: " + str(self.ping.get('ping_count'))) if self.ping.get('ping_count') else '')
    (print("    Interval: " + str(self.ping.get('ping_interval'))) if self.ping.get('ping_interval') else '')
    print("  Connection configuration:")
    (print("    Primary band: " + str(self.connection.get('primary_band'))) if self.connection.get('primary_band') else '')
    (print("    Secondary band: " + str(self.connection.get('secondary_band'))) if self.connection.get('secondary_band') else '')
    (print("    eNB ID: " + str(self.connection.get('enbid'))) if self.connection.get('enbid') else '')
    print("  Reboot settings:")
    print("    Reboot now: " + str(self.reboot_now))
    print("    Skip reboot: " + str(self.skip_reboot))
    (print("    Min uptime: " + str(self.reboot.get('uptime'))) if self.reboot.get('uptime') else '')
    print("  Reboot on: " + ("ping " if self.reboot['ping'] else '') + ("4G_band " if self.reboot['4G_band'] else '')
      + ("5G_band " if self.reboot['5G_band'] else '') + ("eNB_ID" if self.reboot['enbid'] else ''))
    print('')

# __main__
if __name__ == "__main__":

  config = Configuration()
  if config.general['print_config']:
    config.print_config()
  if config.general['logfile']:
    # DEBUG logs go to console, all other logs to this file
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S', 
      filename=config.general['logfile'], level=logging.INFO)
  if config.reboot_now:
    logging.info('Immediate reboot requested.')
    reboot_requested = True
  else:
    reboot_requested = False

  log_all = False  
  if config.general['log_all']:
    log_all = True
    connection = dict([('4G', ''), ('5G', ''), ('enbid', ''), ('ping', '')])

  tc_control = TrashCanController(config.login['username'], config.login['password'])

  if not reboot_requested:

    # Check for eNB ID if an eNB ID was supplied & reboot on eNB ID wasn't False in the .env
    if config.connection['enbid'] and config.reboot['enbid'] or log_all:
      site_meta = tc_control.get_site_info()
      connection['enbid'] = site_meta['eNBID']
      if (site_meta['eNBID'] != config.connection['enbid']) and config.reboot['enbid']:
        msg = 'Not on eNB ID ' + str(config.connection['enbid']) + ', on ' + str(site_meta['eNBID']) + '.'
        print(msg)
        logging.info(msg)
        reboot_requested = True
      else:
        print('eNB ID check passed, on ' + str(site_meta['eNBID']) + '.')

    # Check for preferred bands regardless of reboot on band mismatch
    if config.reboot['4G_band'] or config.reboot['5G_band'] or log_all:
      signal_info = tc_control.get_signal_info()

      if config.connection['primary_band'] or log_all:
        primary_band = config.connection['primary_band']
        band_4g = signal_info['cell_LTE_stats_cfg'][0]['stat']['Band']
        connection['4G'] = band_4g
        if (band_4g not in primary_band) and config.reboot['4G_band']:
          msg = 'Not on ' + ('one of ' if len(primary_band) > 1 else '') + ', '.join(primary_band) + '.'
          print(msg)
          logging.info(msg)
          if config.reboot['4G_band']:
            reboot_requested = True
        else:
          print('Camping on ' + band_4g + '.')

      # 5G has a default value set (n41)
      secondary_band = config.connection['secondary_band']
      band_5g = signal_info['cell_5G_stats_cfg'][0]['stat']['Band']
      connection['5G'] = band_5g
      if band_5g not in secondary_band and config.reboot['5G_band']:
        msg = 'Not on ' + ('one of ' if len(secondary_band) > 1 else '') + ', '.join(secondary_band) + '.'
        print(msg)
        logging.info(msg)
        if config.reboot['5G_band']:
          reboot_requested = True
      else:
        print('Camping on ' + band_5g + '.')

    # Check for successful ping
    if config.reboot['ping']:
      ping_ms = tc_control.ping(config.ping['ping_host'], config.ping['ping_count'], 
        config.ping['ping_interval'], config.ping['interface'])
      if log_all:
        connection['ping'] = ping_ms
      if ping_ms < 0:
        msg = 'Could not ping ' + config.ping['ping_host'] + '.'
        print(msg)
        logging.error(msg)
        if config.reboot['ping']:
          reboot_requested = True

  # Reboot if needed
  if (reboot_requested or log_all):
    connection['uptime'] = tc_control.get_uptime()
  if reboot_requested:
    if config.skip_reboot:
      print('Not rebooting.')
    else:
      msg = 'Reboot requested.'
      print(msg)
      logging.info(msg)

      if config.reboot_now or (connection['uptime'] >= config.reboot['uptime']):
        msg = 'Rebooting.'
        print(msg)
        logging.info(msg)
        tc_control.reboot()
      else:
        msg = 'Uptime threshold not met for reboot.'
        print(msg)
        logging.info(msg)
  else:
    print('No reboot necessary.')
  
  if log_all:
    msg = "4G: {0} |  5G: {1} | eNB ID: {2} | Avg Ping: {3} ms | Uptime: {4} sec".format(
      connection['4G'], connection['5G'], connection['enbid'], connection['ping'], connection['uptime'])
    print(msg)
    logging.info(msg)

