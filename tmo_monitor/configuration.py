import argparse
import getpass
import logging
import os
import sys
from dotenv import load_dotenv, find_dotenv
from .utility import print_and_log
from .gateway.model import GatewayModel

class Configuration:
  def __init__(self):
    # Set default values
    self.reboot_now = False
    self.skip_reboot = False
    self.login = dict([('username', 'admin'), ('password', '')])
    self.ping = dict([('interface', ''), ('ping_host', 'google.com'), ('ping_count', 1), ('ping_interval', 10)])
    self.connection = dict([('primary_band', None), ('secondary_band', ['n41']), ('enbid', None), ('uptime', '')])
    self.reboot = dict([('uptime', 90), ('ping', True), ('4G_band', True), ('5G_band', True), ('enbid', True)])
    self.general = dict([('print_config', False), ('logfile', ''), ('log_all', False), ('log_delta', False)])
    self.model = GatewayModel.NOKIA

    # Command line arguments override defaults & .env file
    self.read_environment()
    args = self.parse_commandline()
    self.parse_arguments(args)

    if self.skip_reboot and self.reboot_now:
      print_and_log('Incompatible options: --reboot and --skip-reboot', 'ERROR')
      if sys.stdin and sys.stdin.isatty():
        self.parser.print_help(sys.stderr)
      sys.exit(2)
    if self.skip_reboot:
      for var in {'ping', '4G_band', '5G_band', 'enbid'}:
        self.reboot[var] = False
    if not self.login['password']:
      self.login['password'] = getpass.getpass('Password: ')


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
    tmp = os.environ.get('tmo_min_uptime')
    if tmp != None:
      self.reboot['uptime'] = tmp

    # Default all reboot options to true, .env file can override to false
    for var in {'ping', '4G_band', '5G_band', 'enbid'}:
      tmp = os.environ.get('tmo_' + var + '_reboot')
      if tmp != None:
        if tmp.lower() == 'false':
          self.reboot[var] = False
        else:
          self.reboot[var] = True

    tmp = os.environ.get('tmo_skip_reboot')
    if tmp != None:
      if tmp.lower() == 'true':
        self.skip_reboot = True
      else:
        self.skip_reboot = False
    tmp = os.environ.get('tmo_logfile')
    if tmp != None:
        self.general['logfile'] = tmp
    for var in {'print_config', 'log_all', 'log_delta'}:
      tmp = os.environ.get('tmo_' + var)
      if tmp != None:
          if tmp.lower() == 'true':
            self.general[var] = True
          else:
            self.general[var] = False
    tmp = os.environ.get('tmo_model')
    if tmp != None:
      self.model = GatewayModel(tmp)

  def parse_commandline(self):
    self.parser = argparse.ArgumentParser(description='Check T-Mobile Home Internet cellular band(s) and connectivity and reboot if necessary')
    # login settings
    self.parser.add_argument('username', type=str, help='the username (most likely "admin")', nargs='?')
    self.parser.add_argument('password', type=str, help='the administrative password (will be requested at runtime if not passed as argument)', nargs='?')
    # ping configuration
    self.parser.add_argument('-I', '--interface', type=str, help='the network interface to use for ping. pass the source IP on Windows')
    self.parser.add_argument('-H', '--ping-host', type=str, default=self.ping['ping_host'], help='the host to ping (defaults to google.com)')
    self.parser.add_argument('--ping-count', type=int, default=self.ping['ping_count'], help='how many ping health checks to perform (defaults to 1)')
    self.parser.add_argument('--ping-interval', type=int, default=self.ping['ping_interval'], help='how long in seconds to wait between ping health checks (defaults to 10)')
    # reboot settings
    self.parser.add_argument('-R', '--reboot', action='store_true', help='skip health checks and immediately reboot gateway')
    self.parser.add_argument('-r', '--skip-reboot', action='store_true', help='skip rebooting gateway')
    self.parser.add_argument('--skip-bands', action='store_true', help='skip check for connected 4g band')
    self.parser.add_argument('--skip-5g-bands', action='store_true', help='skip check for connected 5g band')
    self.parser.add_argument('--skip-ping', action='store_true', help='skip check for successful ping')
    self.parser.add_argument('--skip-enbid', action='store_true', help='skip check for connected eNB ID')
    self.parser.add_argument('--uptime', type=int, default=self.reboot['uptime'], help='how long the gateway must be up before considering a reboot (defaults to 90 seconds)')
    # connection configuration
    self.parser.add_argument('-4', '--4g-band', type=str, action='append', dest='primary_band', default=None, choices=['B2', 'B4', 'B5', 'B12', 'B13', 'B25', 'B26', 'B41', 'B46', 'B48', 'B66', 'B71'], help='the 4g band(s) to check')
    self.parser.add_argument('-5', '--5g-band', type=str, action='append', dest='secondary_band', default=None, choices=['n41', 'n71'], help='the 5g band(s) to check (defaults to n41)')
    self.parser.add_argument('--enbid', type=int, default=self.connection['enbid'], help='check for a connection to a given eNB ID')
    # general configuration
    self.parser.add_argument('--print-config', action='store_true', default=self.general['print_config'], help='output configuration settings')
    self.parser.add_argument('--logfile', type=str, default=self.general['logfile'], help='output file for logging')
    self.parser.add_argument('--log-all', action='store_true', default=self.general['log_all'], help='always write connection details to logfile')
    self.parser.add_argument('--log-delta', action='store_true', default=self.general['log_delta'], help='write connection details to logfile on change')
    self.parser.add_argument('--model', type=str, default=self.model, choices=[model.value for model in GatewayModel], help='the gateway model (defaults to NOK5G21)')
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
    self.general['logfile'] = args.logfile
    for var in {'print_config', 'log_all', 'log_delta'}:
      tmp = getattr(args, var)
      self.general[var] = tmp

    if args.uptime != None:
      self.reboot['uptime'] = args.uptime

    # At this point in the script self.reboot[*] defaults to True unless overridden in .env file

    # Reboot on ping by default, override for args.skip_ping
    if args.skip_ping == True:
      self.reboot['ping'] = False

    # Reboot on primary (4G) band only if one is specified & no overrides
    if self.connection['primary_band'] == None or args.skip_bands == True:
      self.reboot['4G_band'] = False

    # Secondary band has default (n41). Reboot only if skipped on command line
    if args.skip_5g_bands == True:
      self.reboot['5G_band'] = False

    # Reboot on enbid only if one is specified & no overrides
    if self.connection['enbid'] == None or args.skip_enbid == True:
      self.reboot['enbid'] = False

    if args.skip_reboot == True:
      self.skip_reboot = True
    if args.reboot == True:
      self.reboot_now = True

    if args.model is not None:
      self.model = GatewayModel(args.model)

  def print_config(self):
    print("Script configuration:")
    print("  Gateway model: " + self.model.value)
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
    print("  General settings:")
    print("    Log file: " + str(self.general['logfile']))
    print("    Log all: " + str(self.general['log_all']))
    print("    Log delta: " + str(self.general['log_delta']))
    print('')