import platform
import requests
import re
import shutil
import subprocess
import time
import sys

class ControllerBase:
  # functions that don't touch the API
  def ping(self, ping_host, ping_count, ping_interval, interface = None, ping_6 = False):
    is_win = platform.system() == 'Windows'
    is_mac = platform.system() == 'Darwin'

    ping_cmd = []
    extra_flags = []

    # Handle IPv6 support - use ping6 binary or ping -6 flag
    ping_bin = 'ping'
    if ping_6:
      if shutil.which('ping6') is not None:
        ping_bin = 'ping6'
      else:
        extra_flags.append('-6')
    # Explicitly use -4 flag for IPv4 except for Mac OS X
    elif not is_mac:
      extra_flags.append('-4')

    # Add optional interface flag
    if interface:
      extra_flags.append('-S' if is_win else '-I')
      extra_flags.append(interface)

    # Combine base command with extra flags
    ping_cmd.append(ping_bin)
    ping_cmd = ping_cmd + extra_flags

    # Specify ping count
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
      if is_win and 'Destination host unreachable' in str(ping_exec.stdout):
        return -1
      pattern = b'(?:rtt|round-trip) min/avg/max(?:/(?:mdev|stddev))? = \d+.\d+/(\d+.\d+)/\d+.\d+(?:/\d+.\d+)? ms'
      if is_win:
        pattern = b'Minimum = \d+ms, Maximum = \d+ms, Average = (\d+)ms'
      ping_ms = re.search(pattern, ping_exec.stdout)
      return round(float(ping_ms.group(1)))

    for i in range (ping_count):
      result = ping_time(i)
      if result > 0:
        return result
    return -1

  def http_check(self, target, interface = None):
    r = requests.get(target)
    return r.status_code