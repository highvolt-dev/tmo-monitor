import platform
import re
import subprocess
import time

class ControllerBase:
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
      ping_exec = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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