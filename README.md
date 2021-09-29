# tmo-monitor
A lightweight Python 3 script that can monitor the T-Mobile Home Internet Nokia 5G Gateway for band and connectivity and reboot as needed.

Currently checks for n41 5G signal and connectivity to either google.com or a configurable host via ping.

Windows is not currently supported, but should work well with *nix OSes.

## Getting Started

### Install dependencies

`pip install -r requirements.txt`

### Mark as executable

`chmod +x ./tmo-monitor.py`

## Usage
```
usage: tmo-monitor.py [-h] [-I INTERFACE] [-H PING_HOST] username password

Check T-Mobile Home Internet 5g band and connectivity and reboot if necessary

positional arguments:
  username              the username. should be admin
  password              the administrative password

optional arguments:
  -h, --help            show this help message and exit
  -I INTERFACE, --interface INTERFACE
                        the network interface to use for ping
  -H PING_HOST, --ping-host PING_HOST
  -R, --reboot          skip health checks and immediately reboot gateway
```

## Options
**Interface:** `--interface`
    Can be used to specify the network interface used by the ping command. Useful if T-Mobile Home Internet is not your default network interface: e.g., this is running on a dual WAN router.
    
**Ping Host:** `--ping-host`
    Defaults to `google.com` - override if you'd like to ping an alternate host to determine internet connectivity.
    
**Reboot:** `--reboot`
    Skip health checks and immediately reboot gateway.

## Known Issues
Windows OS ping implementation is not supported.

## Roadmap

(Not yet implemented):
- Specify desired band locking
  - 4g
  - 5g
- Disable band locking check
- Disable ping/connectivity check
- Alternate connectivity checks
- Disable reboot behavior
- systemd service configuration

## Tip
Run this script with either a cronjob or as a systemd service to implement periodic recurring T-Mobile Home Internet health checks with automatic rebooting.
