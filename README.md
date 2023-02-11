<p align="center">
  <img src="tmo-monitor-logo.png" width="256" height="256" alt="tmo-monitor logo" style="background-color: #ffffff; border: 5px solid white; border-radius: 16px;">
</p>

# tmo-monitor

A lightweight, cross-platform Python 3 script that can monitor the T-Mobile Home Internet Nokia, Arcadyan, and Sagecom 5G Gateways for 4G/5G bands, cellular site (tower), and internet connectivity and reboots as needed or on-demand.

By default, checks for n41 5G signal and connectivity to google.com via ping.

## Getting Started

### Install dependencies

`pip3 install .`

The command will then be available anywhere as `tmo-monitor.py`.

#### Windows

1. On Windows, open the folder where you downloaded the project.
2. Click `File` > `Open Windows PowerShell`
3. Run the above `pip3 install .` command.
4. To use, either:
    - Run `cmd.exe` within PowerShell first
    - Open `cmd.exe` (Command Prompt) instead of PowerShell
    - Run `python bin/tmo-monitor.py` in PowerShell from inside the project directory

When in doubt, consult this document or run `tmo-monitor.py --help`.

## Usage

### Command line usage
```
usage: tmo-monitor.py [-h] [--connectivity-check {ping,http}]
                      [-I INTERFACE]
                      [--http-target HTTP_TARGET] [--status-code {[100,600)}]
                      [-H PING_HOST] [--ping-count PING_COUNT] [--ping-interval PING_INTERVAL] [-6]
                      [-R] [-r]
                      [--skip-bands] [--skip-5g-bands] [--skip-connectivity-check] [--skip-enbid]
                      [--uptime UPTIME]
                      [-4 {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}] [-5 {n41,n71}]
                      [--enbid ENBID]
                      [--print-config]
                      [--logfile LOGFILE] [--log-all] [--log-delta] [--syslog]
                      [--model {NOK5G21,ARCKVD21,FAST5688W}]
                      [username] [password]

Check T-Mobile Home Internet cellular band(s) and connectivity and reboot if necessary

positional arguments:
  username              the username (most likely "admin")
  password              the administrative password (will be requested at runtime if not passed as argument)

optional arguments:
  -h, --help            show this help message and exit
  --connectivity-check {ping,http}
                        type of connectivity check to perform (defaults to ping)
  -I INTERFACE, --interface INTERFACE
                        the network interface to use for ping. pass the source IP on Windows
  --http-target HTTP_TARGET
                        the URL to perform a http check against (defaults to https://google.com/generate_204)
  --status-code {[100,600)}
                        expected HTTP status code for http connectivity check (defaults to 204)
  -H PING_HOST, --ping-host PING_HOST
                        the host to ping (defaults to google.com)
  --ping-count PING_COUNT
                        how many ping health checks to perform (defaults to 1)
  --ping-interval PING_INTERVAL
                        how long in seconds to wait between ping health checks (defaults to 10)
  -6, --ping-6          use IPv6 ping
  -R, --reboot          skip health checks and immediately reboot gateway
  -r, --skip-reboot     skip rebooting gateway
  --skip-bands          skip check for connected 4g band
  --skip-5g-bands       skip check for connected 5g band
  --skip-connectivity-check, --skip-ping
                        skip connectivity check
  --skip-enbid          skip check for connected eNB ID
  --uptime UPTIME       how long the gateway must be up before considering a reboot (defaults to 90 seconds)
  -4 {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}, --4g-band {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}
                        the 4g band(s) to check
  -5 {n41,n71}, --5g-band {n41,n71}
                        the 5g band(s) to check (defaults to n41)
  --enbid ENBID         check for a connection to a given eNB ID
  --print-config        output configuration settings
  --logfile LOGFILE     output file for logging
  --log-all             always write connection details to logfile
  --log-delta           write connection details to logfile on change
  --syslog              log to syslog
  --model {NOK5G21,ARCKVD21,FAST5688W}
                        the gateway model (defaults to NOK5G21)
```

## Options

### Gateway Model
**Gateway Model:** `--model`

By default, the script will assume the silver-colored Nokia NOK5G21 gateway is being used.

Valid values are `NOK5G21` for the Nokia gateway, `ARCKVD21` for the square, black-colored Arcadyan gateway without top vent holes, or `FAST5688W` for the square, black-colored Sagecom gateway with top vent holes.

### Connectivity check
**Mode:** `--connectivity-check`
    Defaults to `ping`. Can instead use a HTTP(S) based health check with the `http` value. The `http` health check defaults to checking `https://google.com/generate_204` and checking its status code.

**Interface:** `-I --interface`
    Can be used to specify the network interface used by the ping command. Useful if T-Mobile Home Internet is not your default network interface: e.g., this is running on a dual WAN router. On Windows, pass the source IP address to use. `http` connectivity checks will be dictated by system routing rules.

### HTTP check
**Target:** `--http-target`
    Defaults to `https://google.com/generate_204` - both `http` and `https` targets are supported by the `http` value of the `--connectivity-check` flag.

**Status Code:** `--status-code`
    Defaults to `204` for use with `https://google.com/generate_204` - in most common use cases, a `200` status code is expected instead. Expects a numeric value between 100-599 (inclusive).

### Ping options

`ping` checks are the default connectivity check in `tmo-monitor`. It's possible to use HTTP(S)-based checks instead. Refer to the `--connectivity-check` flag.

**Ping Host:** `-H --ping-host`
    Defaults to `google.com` - override if you'd like to ping an alternate host to determine internet connectivity. Must specify a host if flag is provided - you can simply omit the flag if you'd like to use the default google.com ping check.

**Ping Count:** `--ping-count`
    Defaults to `1` - override if you'd like to perform multiple ping checks before rebooting. Short-circuits if a successful ping is encountered. Will reboot if all fail.

**Ping Interval:** `--ping-interval`
    Defaults to `10` seconds - override if you'd like to use a different interval.

**Ping v6:** `-6 --ping-6`
    Use IPv6 ping.

### Reboot options
**Reboot:** `-R --reboot`
    Skip health checks and immediately reboot gateway.

**Skip Reboot:** `-r --skip-reboot`
    Skip rebooting gateway.

**Skip Bands:** `--skip-bands`
    Skip check for connected 4g band.

**Skip 5g Bands:** `--skip-5g-bands`
    Skip check for connected 5g band.

**Skip Ping:** `--skip-connectivity-check --skip-ping`
    Skip check for successful connectivity check.

**Uptime Threshold:** `--uptime`
    Defaults to 90 seconds - Specify a required uptime for an implicit reboot to occur. Intended to allow sufficient time to establish a connection and stabilize band selection. Setting is used to avoid boot looping, but is not respected when the `--reboot` flag is used.

### Connection configuration
**4G Band Checking:** `-4 --4g-band`
    Specify a 4G band you expect the gateway to be connected to. Repeat the flag to allow multiple acceptable bands. Case-sensitive.

**5G Band Checking:** `-5 --5g-band`
    Defaults to n41 - Specify a 5G band you expect the gateway to be connected to. Repeat the flag to allow multiple acceptable bands. Case-sensitive.

**eNB ID:** `--enbid`
    Specify the desired cell site you expect the gateway to be connected to. Expects a numeric eNB ID to be provided. [cellmapper.net](https://www.cellmapper.net) is a helpful resource for finding eNB ID values for nearby cell sites.

### General settings

**Logfile:** `--logfile LOGFILE`
    Output file for logging. Defaults to `tmo-monitor.log`

**Log all:** `--log-all`
    Always write connection details to logfile. Checks all configuration settings.

**Log delta:** `--log-delta`
    Write connection details to logfile on change of any configuration setting or long ping time.

### Default settings
- Username == admin
- Password -> interactive prompt
- 5G band == n41
- Reboot on failure to ping google.com

### Environment (`.env`) options

The script is normally run in batch mode, such as scheduled through a `cron` job. Interactive command-line options are meant to be used as overrides to defaults or environment settings.

A common usage pattern would be to configure the script using a `.env` file to reboot on 5G band and wifi check. When messing with the settings, a user might want to specify `--skip-reboot`. When a user knows that the reboot is needed they might specify `--reboot` for an immediate reboot.

- Default settings have the lowest precendence.
- Environment settings--whether in the shell environment or a `.env` file--override the defaults
- Command line options have the highest precedence and override both default settings and environment settings


Environment settings are meant to be declarative. They fall into four categories:

- Login settings (username, password)
- Configuration settings
    - Ping settings (target host/interface, number of pings, interval)
    - Connection settings (preferred band, eNB ID, etc.)
- Reboot settings: request reboot on any number of failed checks.
    - Skip reboot overrides all reboot requests
    - Reboot interval overrides all reboot requests
    - There is no "reboot immediately" option
- General settings:
    - Default output/silent mode _(not yet implemented)_
    - Logging settings


## Exit Status

tmo-monitor uses the following exit status codes:

- Clean execution: 0
-  `GENERAL_ERROR`: 1
-  `CONFIGURATION_ERROR`: 2
-  `API_ERROR`: 3
-  `REBOOT_PERFORMED`: 4


## Roadmap

(Not yet implemented):
- Alternate connectivity checks
- systemd service configuration

## Tip
Run this script with either a cronjob or as a systemd service to implement periodic recurring T-Mobile Home Internet health checks with automatic rebooting.
