#!/usr/bin/env python3
# Start by getting signal metrics
import logging
import logging.handlers
import os
import platform
import sys
import tailer
from parse import *
from tmo_monitor.gateway.model import GatewayModel
from tmo_monitor.configuration import Configuration
from tmo_monitor.gateway.arcadyan import CubeController
from tmo_monitor.gateway.nokia import TrashCanController
from tmo_monitor.status import ExitStatus

# __main__
if __name__ == "__main__":

  config = Configuration()
  if config.general['print_config']:
    config.print_config()
  # Set up logging for console
  root_logger = logging.getLogger()
  root_logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y/%m/%d %H:%M:%S')
  console_logger = logging.StreamHandler()
  console_logger.setFormatter(formatter)
  root_logger.addHandler(console_logger)
  if config.general['logfile']:
    file_logger = logging.FileHandler(config.general['logfile'])
    file_logger.setLevel(logging.INFO)
    file_logger.setFormatter(formatter)
    root_logger.addHandler(file_logger)
    logging.debug('Enabled file logging to {}'.format(config.general['logfile']))
  if config.general['syslog']:
    syslog_handler_opts = {}
    syslog_logging_details = ''
    if platform.system() != 'Windows':
      for syslog_socket in ['/dev/log', '/var/run/syslog']:
        if os.path.exists(syslog_socket):
          syslog_handler_opts['address'] = syslog_socket
          syslog_logging_details = ' via {}'.format(syslog_socket)
          break
    syslog_logger = logging.handlers.SysLogHandler(**syslog_handler_opts)
    syslog_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    syslog_logger.setFormatter(syslog_formatter)
    syslog_logger.setLevel(logging.INFO)
    syslog_logger.ident = 'tmo-monitor[{}]: '.format(os.getpid())
    root_logger.addHandler(syslog_logger)
    logging.debug('Enabled syslog logging{}'.format(syslog_logging_details))
  if config.reboot_now:
    logging.info('Immediate reboot requested.')
    reboot_requested = True
  else:
    reboot_requested = False

  log_all = False
  connection = dict([('4G', ''), ('5G', ''), ('enbid', ''), ('ping', '')])
  if config.general['log_all'] or config.general['log_delta']:
    log_all = True

  if config.model == GatewayModel.NOKIA:
    gw_control = TrashCanController(config.login['username'], config.login['password'])
  # The Arcadyan and Sagecom gateways appear to conform to the same API
  elif config.model in [GatewayModel.ARCADYAN, GatewayModel.SAGECOM]:
    gw_control = CubeController(config.login['username'], config.login['password'])
  else:
    raise Exception('Unsupported Gateway Model')

  if not reboot_requested:

    # Check for eNB ID if an eNB ID was supplied & reboot on eNB ID wasn't False in the .env
    if config.connection['enbid'] and config.reboot['enbid'] or log_all:
      site_meta = gw_control.get_site_info()
      connection['enbid'] = site_meta['eNBID']
      if (site_meta['eNBID'] != config.connection['enbid']) and config.reboot['enbid']:
        logging.info('Not on eNB ID ' + str(config.connection['enbid']) + ', on ' + str(site_meta['eNBID']) + '.')
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
          logging.info('Not on ' + ('one of ' if len(primary_band) > 1 else '') + ', '.join(primary_band) + '.')
          if config.reboot['4G_band']:
            reboot_requested = True
        else:
          print('Camping on ' + band_4g + '.')

      # 5G has a default value set (n41)
      secondary_band = config.connection['secondary_band']
      band_5g = signal_info['5G']
      connection['5G'] = band_5g
      if band_5g not in secondary_band and config.reboot['5G_band']:
        logging.info('Not on ' + ('one of ' if len(secondary_band) > 1 else '') + ', '.join(secondary_band) + '.')
        if config.reboot['5G_band']:
          reboot_requested = True
      else:
        print('Camping on ' + band_5g + '.')

    # Check for successful ping
    ping_ms = gw_control.ping(config.ping['ping_host'], config.ping['ping_count'], config.ping['ping_interval'], config.connectivity['interface'], config.ping['ping_6'])
    if log_all:
      connection['ping'] = ping_ms
    if ping_ms < 0 and config.connectivity['connectivity_check'] == 'ping':
      logging.error('Could not ping ' + config.ping['ping_host'] + '.')
      if config.reboot['ping']:
        reboot_requested = True

    # Check for successful http check
    if config.connectivity['connectivity_check'] == 'http':
      status_code = gw_control.http_check(config.http['http_target'])
      if status_code != config.http['status_code']:
        logging.error('Status code failed check for ' + config.http['http_target'] + ' - received status code ' + str(status_code))
        if config.reboot['http']:
          reboot_requested = True

  # Reboot if needed
  reboot_performed = False
  if (reboot_requested or log_all):
    connection['uptime'] = gw_control.get_uptime()
  if reboot_requested:
    if config.skip_reboot:
      logging.info('Not rebooting.')
    else:
      logging.info('Reboot requested.')

      if config.reboot_now or (connection['uptime'] >= config.reboot['uptime']):
        logging.info('Rebooting.')
        gw_control.reboot()
        reboot_performed = True
      else:
        logging.info('Uptime threshold not met for reboot.')
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
            logging.info("4G connection is {0}, was {1}".format(connection['4G'], data[1]))
            config.general['log_all'] = True
          if data[2] != connection['5G']:
            logging.info("5G connection is {0}, was {1}".format(connection['5G'], data[2]))
            config.general['log_all'] = True
          if int(data[3]) != connection['enbid']:
            logging.info("eNB ID is {0}, was {1}".format(connection['enbid'], data[3]))
            config.general['log_all'] = True
          if int(data[4]) * 3 < connection['ping']:
            logging.info("Ping ms {0}, over 3x {1} ms".format(connection['ping'], data[4]))
            config.general['log_all'] = True
          if int(data[5]) > connection['uptime']:
            logging.info("Uptime {0} sec, less than {1} sec".format(connection['uptime'], data[5]))
            config.general['log_all'] = True
          break

  if log_all and config.general['log_all']:
    if config.general['logfile'] == '' and not config.general['syslog']:
      logging.error("Logging requested but file or syslog not specified")
    else:
      msg = "4G: {0} | 5G: {1} | eNB ID: {2} | Avg Ping: {3} ms | Uptime: {4} sec".format(
        connection['4G'], connection['5G'], connection['enbid'], connection['ping'], connection['uptime'])
      logging.info(msg)

  if reboot_performed:
    sys.exit(ExitStatus.REBOOT_PERFORMED.value)
