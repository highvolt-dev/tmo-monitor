# tmo-monitor
A lightweight, cross-platform Python 3 script that can monitor the T-Mobile Home Internet Nokia 5G Gateway for 4G/5G bands, cellular site (tower), and internet connectivity and reboots as needed or on-demand.

By default, checks for n41 5G signal and connectivity to google.com via ping.


## API Design for v2

Design philosophy: The script is normally run in batch mode, such as scheduled through a `cron` job. Interactive command-line options are meant to be used as overrides to defaults or environment settings.

A common usage pattern would be to configure the script using a `.env` file to reboot on 5G band and wifi check. When messing with the settings, a user might want to specify `--skip-reboot`. When a user knows that the reboot is needed they might specify `--reboot` for an immediate reboot.

- Default settings have the lowest precendence. 
- Environment settings--whether in the shell environment or a `.env` file--override the defaults
- Command line options override default settings

### Default settings
- Username == admin
- Password -> interactive prompt
- 5G band == n41
- Reboot == on wifi failure

### Environment options
Environment settings are meant to be declarative. They fall into three categories:

- Login settings (isername, password)
- Configuration settings
    - Ping settings (target host/interface, number of pings, interval)
    - Connection settings (preferred band, eNB ID, etc.)
- Reboot settings: request reboot on any number of failed checks.
    - Skip reboot overrides all reboot requests
    - Reboot interval overrides all reboot requests
    - There is no "reboot immediately" option

### Command-line options







## Usage
```
usage: tmo-monitor.py [-h] [-I INTERFACE] [-H PING_HOST] [-R] [-r]
                      [--skip-bands] [--skip-5g-bands] [--skip-ping]
                      [-4 {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}]
                      [-5 {n41,n71}] [--uptime UPTIME] [--enbid ENBID]
                      username [password]

Check T-Mobile Home Internet cellular band(s) and connectivity and reboot if necessary

positional arguments:
  username              the username (most likely "admin")
  password              the administrative password (will be requested at
                        runtime if not passed as argument)

optional arguments:
  -h, --help            show this help message and exit
  -I INTERFACE, --interface INTERFACE
                        the network interface to use for ping. pass the source
                        IP on Windows
  -H PING_HOST, --ping-host PING_HOST
                        the host to ping (defaults to google.com)
  --ping-count
                        how many ping health checks to perform (defaults to 1)
  --ping-interval
                        how long in seconds to wait between ping health checks (defaults to 10)
  -R, --reboot          skip health checks and immediately reboot gateway
  -r, --skip-reboot     skip rebooting gateway
  --skip-bands          skip check for connected band
  --skip-5g-bands       skip check for connected 5g band
  --skip-ping           skip check for successful ping
  -4 {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}, --4g-band {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}
                        the 4g band(s) to check
  -5 {n41,n71}, --5g-band {n41,n71}
                        the 5g band(s) to check (defaults to n41)
  --uptime UPTIME       how long the gateway must be up before considering a
                        reboot (defaults to 90 seconds)
  --enbid ENBID         check for a connection to a given eNB ID
```

## Options
**Interface:** `-I --interface`
    Can be used to specify the network interface used by the ping command. Useful if T-Mobile Home Internet is not your default network interface: e.g., this is running on a dual WAN router. On Windows, pass the source IP address to use.

**Ping Host:** `-H --ping-host`
    Defaults to `google.com` - override if you'd like to ping an alternate host to determine internet connectivity. Must specify a host if flag is provided - you can simply omit the flag if you'd like to use the default google.com ping check.

**Ping Count:** `--ping-count`
    Defaults to `1` - override if you'd like to perform multiple ping checks before rebooting.

**Ping Interval:** `--ping-interval`
    Defaults to `10` seconds - override if you'd like to use a different interval.

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

**Uptime Threshold:** `--uptime`
    Defaults to 90 seconds - Specify a required uptime for an implicit reboot to occur. Intended to allow sufficient time to establish a connection and stabilize band selection. Setting is used to avoid boot looping, but is not respected when the `--reboot` flag is used.

**eNB ID:** `--enbid`
    Specify the desired cell site you expect the gateway to be connected to. Expects a numeric eNB ID to be provided. [cellmapper.net](https://www.cellmapper.net) is a helpful resource for finding eNB ID values for nearby cell sites.

