# tmo-monitor
A lightweight Python 3 script that can monitor the T-Mobile Home Internet Nokia 5G Gateway for band and connectivity and reboot as needed.

Currently checks for n41 5G signal and connectivity to either google.com or a configurable host via ping.

Windows is not currently supported, but should work well with *nix OSes.

## Getting Started

### Install dependencies

`pip -r requirements.txt`

### Mark as executable

`chmod +x ./tmo-monitor.py`

## Usage
```
usage: tmo-monitor.py [-h] [-u USERNAME] [-p PASSWORD] [-I INTERFACE] [-H PING_HOST] [-g] [-f CREDENTIALS_FILE]
                      [-R]

Check T-Mobile Home Internet 5g band and connectivity and reboot if necessary

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        the administrative username (defaults to "admin")
  -p PASSWORD, --password PASSWORD
                        the administrative password (will be prompted if not passed as argument)
  -I INTERFACE, --interface INTERFACE
                        the network interface to use for ping
  -H PING_HOST, --ping-host PING_HOST
                        the host to ping (defaults to google.com)
  -g, --generate-credentials
                        generate credentials and exit (saved as credentials.json unless used in combination with
                        -f)
  -f CREDENTIALS_FILE, --credentials-file CREDENTIALS_FILE
                        file from which to save/load saved credentials
  -R, --reboot          skip health checks and immediately reboot gateway
```

## Options
**Interface:** `--interface`

  Can be used to specify the network interface used by the ping command. Useful if T-Mobile Home Internet is not your default network interface: e.g., this is running on a dual WAN router.
    
**Ping Host:** `--ping-host`

  Defaults to `google.com` - override if you'd like to ping an alternate host to determine internet connectivity.
    
**Reboot:** `--reboot`

  Skip health checks and immediately reboot gateway.

**Generate Credentials File:** `--generate-credentials`

  Generate credentials and save to file (defaults to `credentials.json`, but can be specified with `--credentials-file <filename.json>`)

**Load Credentials From File:** `--credentials-file <filename.json>`

  Load saved credentials from file (**alternate use**: specifies file to which credentials should be saved if used in combination with `--generate-credentials`)

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
