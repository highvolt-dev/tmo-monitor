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

def reboot():
  nonce_request = requests.get('http://192.168.12.1/login_web_app.cgi?nonce')
  nonce_request.raise_for_status()
  nonce_response = nonce_request.json()

  s = sha256(args.username, args.password)
  r = sha256url(s, nonce_response['nonce'])
  login_request_body = {}
  login_request_body['userhash'] = sha256url(args.username, nonce_response['nonce'])
  login_request_body['RandomKeyhash'] = sha256url(nonce_response['randomKey'], nonce_response['nonce'])
  login_request_body['response'] = r
  login_request_body['nonce'] = base64url_escape(nonce_response['nonce'])

  l = b64encode(secrets.token_bytes(16)).decode('utf-8')
  c = b64encode(secrets.token_bytes(16)).decode('utf-8')
  login_request_body['enckey'] = base64url_escape(l)
  login_request_body['enciv'] = base64url_escape(c)

  login_request = requests.post('http://192.168.12.1/login_web_app.cgi', data=login_request_body)
  login_request.raise_for_status()
  jar = requests.cookies.RequestsCookieJar()
  jar.set('sid', login_request.cookies['sid'], domain='192.168.12.1', path='/')
  jar.set('lsid', login_request.cookies['lsid'], domain='192.168.12.1', path='/')
  login_response = login_request.json()
  csrf_token = login_response['token']

  reboot_request = requests.post('http://192.168.12.1/reboot_web_app.cgi', data={'csrf_token': csrf_token}, cookies=jar)
  reboot_request.raise_for_status()

def base64url_escape(b64):
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

def sha256(val1, val2):
  hash = hashlib.sha256()
  hash.update((val1 + ':' + val2).encode())
  return b64encode(hash.digest()).decode('utf-8')

def sha256url(val1, val2):
  return base64url_escape(sha256(val1, val2))

def ping(args):
  is_win = platform.system() == 'Windows'
  ping_cmd = ['ping']
  if args.interface:
    ping_cmd.append('-S' if is_win else '-I')
    ping_cmd.append(args.interface)
  ping_cmd.append('-n' if is_win else '-c')
  ping_cmd.append('1')
  ping_cmd.append(args.ping_host)
  ping_exec = subprocess.run(ping_cmd, capture_output=True)
  print(ping_exec.stdout.decode('utf-8'))
  if is_win and 'Destination host unreachable' in str(ping_exec.stdout):
    return False
  else:
    return ping_exec.returncode == 0

def get_uptime():
    uptime_req = requests.get('http://192.168.12.1/dashboard_device_info_status_web_app.cgi')
    uptime_req.raise_for_status()
    return uptime_req.json()['device_app_status'][0]['UpTime']

parser = argparse.ArgumentParser(description='Check T-Mobile Home Internet 5g band and connectivity and reboot if necessary')
parser.add_argument('username', type=str, help='the username. should be admin')
parser.add_argument('password', type=str, help='the administrative password')
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
args = parser.parse_args()

if args.skip_reboot and args.reboot:
  print('Incompatible options: --reboot and --skip-reboot\n', file=sys.stderr)
  parser.print_help(sys.stderr)
  sys.exit(2)

if args.secondary_band is None:
  args.secondary_band = ['n41']

reboot_requested = args.reboot

if not args.skip_bands and not reboot_requested:
  signal_request = requests.get('http://192.168.12.1/fastmile_radio_status_web_app.cgi')
  signal_request.raise_for_status()
  signal_info = signal_request.json()
  if args.primary_band:
    band_4g = signal_info['cell_LTE_stats_cfg'][0]['stat']['Band']
    if band_4g not in args.primary_band:
      print('Not on ' + ('one of ' if len(args.primary_band) > 1 else '') + ', '.join(args.primary_band) + '.' + (' Reboot requested.' if not args.skip_reboot else ''))
      reboot_requested = True
    else:
      print('Camping on ' + band_4g + '.' + (' Not rebooting.' if not args.skip_reboot else ''))

  if not args.skip_5g_bands and args.secondary_band:
    band_5g = signal_info['cell_5G_stats_cfg'][0]['stat']['Band']
    if band_5g not in args.secondary_band:
      print('Not on ' + ('one of ' if len(args.secondary_band) > 1 else '') + ', '.join(args.secondary_band) + '.' + (' Reboot requested.' if not args.skip_reboot else ''))
      reboot_requested = True
    else:
      print('Camping on ' + band_5g + '.' + (' Not rebooting.' if not args.skip_reboot else ''))


if not args.skip_ping and not reboot_requested and not ping(args):
  print('Could not ping ' + args.ping_host + '. reboot requested')
  reboot_requested = True

if args.skip_reboot:
  print('Skipping reboot.')
elif reboot_requested:
  uptime_met = args.reboot or get_uptime() >= args.uptime
  if uptime_met:
    print('Rebooting.')
    reboot()
  else:
    print('Uptime threshold not met for reboot.')
else:
  print('No reboot necessary.')
