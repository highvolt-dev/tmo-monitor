#!/usr/bin/env python3
# Start by getting signal metrics
import os
import requests
import subprocess
import hashlib
from base64 import b64encode
import secrets
import argparse

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

parser = argparse.ArgumentParser(description='Check T-Mobile Home Internet 5g band and connectivity and reboot if necessary')
parser.add_argument('username', type=str, help='the username. should be admin')
parser.add_argument('password', type=str, help='the administrative password')
parser.add_argument('-I', '--interface', type=str, help='the network interface to use for ping')
parser.add_argument('-H', '--ping-host', type=str, default='google.com', help='the host to ping')
parser.add_argument('-R', '--reboot', action="store_true", help='skip health checks and immediately reboot gateway')
parser.add_argument('--skip-bands', action="store_true", help='skip check for connected band')
args = parser.parse_args()

reboot_requested = args.reboot

if not args.skip_bands and not reboot_requested:
  signal_request = requests.get('http://192.168.12.1/fastmile_radio_status_web_app.cgi')
  signal_request.raise_for_status()
  signal_info = signal_request.json()
  band_5g = signal_info['cell_5G_stats_cfg'][0]['stat']['Band']
  if band_5g != 'n41':
    print('Not on n41. Reboot requested.')
    reboot_requested = True
  else:
    print('Camping on n41. Not rebooting.')

ping_cmd = ['ping']
if args.interface:
  ping_cmd.append('-I')
  ping_cmd.append(args.interface)
ping_cmd.append('-c')
ping_cmd.append('1')
ping_cmd.append(args.ping_host)

if not reboot_requested and subprocess.call(ping_cmd) != 0:
  print('Could not ping ' + args.ping_host + '. reboot requested')
  reboot_requested = True

if reboot_requested:
  print('Rebooting.')
  reboot()
else:
  print('No reboot necessary.')
