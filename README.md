# tmo-monitor
A lightweight Python 3 script that can monitor the T-Mobile Home Internet Nokia 5G Gateway for band and connectivity and reboot as needed.

Currently checks for n41 5G signal and connectivity to either google.com or a configurable host via ping.

Windows is not currently supported, but should work well with *nix OSes.

## Getting Started

### Install dependencies

`pip3 install -r requirements.txt`

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
                        the host to ping
  -R, --reboot          skip health checks and immediately reboot gateway
  -r, --skip-reboot     skip rebooting gateway
  --skip-bands          skip check for connected band
  --skip-5g-bands       skip check for connected 5g band
  --skip-ping           skip check for successful ping
  -4 {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}, --4g-band {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}
                        the 4g band(s) to check
  -5 {n41,n71}, --5g-band {n41,n71}
                        the 5g band(s) to check (defaults to n41)
```

## Options
**Interface:** `-I --interface`
    Can be used to specify the network interface used by the ping command. Useful if T-Mobile Home Internet is not your default network interface: e.g., this is running on a dual WAN router.
    
**Ping Host:** `-H --ping-host`
    Defaults to `google.com` - override if you'd like to ping an alternate host to determine internet connectivity.
    
**Reboot:** `-R --reboot`
    Skip health checks and immediately reboot gateway.

**Skip Reboot:** `-r --skip-reboot`
    Skip rebooting gateway.

**Skip Bands:** `--skip-bands`
    Skip check for connected band.

**Skip 5g Bands:** `--skip-5g-bands`
    Skip check for connected 5g band.

**Skip Ping:** `--skip-ping`
    Skip check for successful ping.

**4G Band Checking:** `-4 --4g-band`
    Specify a 4G band you expect the gateway to be connected to. Repeat the flag to allow multiple acceptable bands. Case-sensitive.

**5G Band Checking:** `-5 --5g-band`
    Defaults to n41 - Specify a 5G band you expect the gateway to be connected to. Repeat the flag to allow multiple acceptable bands. Case-sensitive.

## Known Issues
Windows OS ping implementation is not supported.

## Roadmap

(Not yet implemented):
- Alternate connectivity checks
- systemd service configuration

## Tip
Run this script with either a cronjob or as a systemd service to implement periodic recurring T-Mobile Home Internet health checks with automatic rebooting.
