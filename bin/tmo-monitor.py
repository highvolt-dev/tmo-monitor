#!/usr/bin/env python3
# Start by getting signal metrics
import logging
import tailer
from parse import *
from tmo_monitor.gateway.model import GatewayModel
from tmo_monitor.configuration import Configuration
from tmo_monitor.utility import print_and_log
from tmo_monitor.gateway.arcadyan import CubeController
from tmo_monitor.gateway.nokia import TrashCanController
from tmo_monitor.status import ExitStatus

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
    print_and_log('Immediate reboot requested.')
    reboot_requested = True
  else:
    reboot_requested = False

  log_all = False
  connection = dict([('4G', ''), ('5G', ''), ('enbid', ''), ('ping', '')])
  if config.general['log_all'] or config.general['log_delta']:
    log_all = True

  if config.model == GatewayModel.NOKIA:
    gw_control = TrashCanController(config.login['username'], config.login['password'])
  elif config.model == GatewayModel.ARCADYAN:
    gw_control = CubeController(config.login['username'], config.login['password'])
  else:
    raise Exception('Unsupported Gateway Model')

  if not reboot_requested:

    # Check for eNB ID if an eNB ID was supplied & reboot on eNB ID wasn't False in the .env
    if config.connection['enbid'] and config.reboot['enbid'] or log_all:
      site_meta = gw_control.get_site_info()
      connection['enbid'] = site_meta['eNBID']
      if (site_meta['eNBID'] != config.connection['enbid']) and config.reboot['enbid']:
        print_and_log('Not on eNB ID ' + str(config.connection['enbid']) + ', on ' + str(site_meta['eNBID']) + '.')
        reboot_requested = True
      else:
        print('eNB ID check passed, on ' + str(site_meta['eNBID']) + '.')

    # Check for preferred bands regardless of reboot on band mismatch
    if config.reboot['4G_band'] or config.reboot['5G_band'] or log_all:
      signal_info = gw_control.get_signal_info()

      if config.connection['primary_band'] or log_all:
        primary_band = config.connection['primary_band']
        band_4g = signal_info['4G']
        connection['4G'] = band_4g
        if (primary_band and band_4g not in primary_band) and config.reboot['4G_band']:
          print_and_log('Not on ' + ('one of ' if len(primary_band) > 1 else '') + ', '.join(primary_band) + '.')
          if config.reboot['4G_band']:
            reboot_requested = True
        else:
          print('Camping on ' + band_4g + '.')

      # 5G has a default value set (n41)
      secondary_band = config.connection['secondary_band']
      band_5g = signal_info['5G']
      connection['5G'] = band_5g
      if band_5g not in secondary_band and config.reboot['5G_band']:
        print_and_log('Not on ' + ('one of ' if len(secondary_band) > 1 else '') + ', '.join(secondary_band) + '.')
        if config.reboot['5G_band']:
          reboot_requested = True
      else:
        print('Camping on ' + band_5g + '.')

    # Check for successful ping
    ping_ms = gw_control.ping(config.ping['ping_host'], config.ping['ping_count'], config.ping['ping_interval'], config.ping['interface'])
    if log_all:
      connection['ping'] = ping_ms
    if ping_ms < 0:
      print_and_log('Could not ping ' + config.ping['ping_host'] + '.', 'ERROR')
      if config.reboot['ping']:
        reboot_requested = True

  # Reboot if needed
  reboot_performed = False
  if (reboot_requested or log_all):
    connection['uptime'] = gw_control.get_uptime()
  if reboot_requested:
    if config.skip_reboot:
      print_and_log('Not rebooting.')
    else:
      print_and_log('Reboot requested.')

      if config.reboot_now or (connection['uptime'] >= config.reboot['uptime']):
        print_and_log('Rebooting.')
        gw_control.reboot()
        reboot_performed = True
      else:
        print_and_log('Uptime threshold not met for reboot.')
  else:
    print('No reboot necessary.')

  if log_all and config.general['log_delta'] and config.general['logfile']:
    # Tail the last 10 lines of the file (to account for logged errors) and reverse to detect the newest logline
    logline = tailer.tail(open(config.general['logfile']), 10)
    logline.reverse()
    for line in logline:
        if line.__contains__('|'):
          print(line)
          data = parse("{0} [INFO] 4G: {1} | 5G: {2} | eNB ID: {3} | Avg Ping: {4} ms | Uptime: {5} sec", line)
          if data[1] != connection['4G']:
            print_and_log("4G connection is {0}, was {1}".format(connection['4G'], data[1]))
            config.general['log_all'] = True
          if data[2] != connection['5G']:
            print_and_log("5G connection is {0}, was {1}".format(connection['5G'], data[2]))
            config.general['log_all'] = True
          if int(data[3]) != connection['enbid']:
            print_and_log("eNB ID is {0}, was {1}".format(connection['enbid'], data[3]))
            config.general['log_all'] = True
          if int(data[4]) * 3 < connection['ping']:
            print_and_log("Ping ms {0}, over 3x {1} ms".format(connection['ping'], data[4]))
            config.general['log_all'] = True
          if int(data[5]) > connection['uptime']:
            print_and_log("Uptime {0} sec, less than {1} sec".format(connection['uptime'], data[5]))
            config.general['log_all'] = True
          break

  if log_all and config.general['log_all']:
    if config.general['logfile'] == '':
      logging.error("Logging requested but file not specified")
    else:
      msg = "4G: {0} | 5G: {1} | eNB ID: {2} | Avg Ping: {3} ms | Uptime: {4} sec".format(
        connection['4G'], connection['5G'], connection['enbid'], connection['ping'], connection['uptime'])
      print_and_log(msg)

  if reboot_performed:
    sys.exit(ExitStatus.REBOOT_PERFORMED.value)