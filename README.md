# tmo-monitor
A lightweight, cross-platform Python 3 script that can monitor the T-Mobile Home Internet Nokia 5G Gateway for 4G/5G bands, cellular site (tower), and internet connectivity and reboots as needed or on-demand.

By default, checks for n41 5G signal and connectivity to google.com via ping.

## Getting Started

### Install dependencies

`pip3 install -r requirements.txt`

### Mark as executable

`chmod +x ./tmo-monitor.py`

## Usage

### Command line usage
```
usage: tmo-monitor.py [-h] [-I INTERFACE] [-H PING_HOST]
                      [--ping-count PING_COUNT]
                      [--ping-interval PING_INTERVAL] [-R] [-r] [--skip-bands]
                      [--skip-5g-bands] [--skip-ping] [--skip-enbid]
                      [--uptime UPTIME]
                      [-4 {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}]
                      [-5 {n41,n71}] [--enbid ENBID] [--logfile LOGFILE]
                      [--log-all] [--log-delta]
                      [username] [password]

Check T-Mobile Home Internet cellular band(s) and connectivity and reboot if
necessary

positional arguments:
  username              the username (most likely "admin")
  password              the administrative password (will be requested at
                        runtime if not passed as argument)

optional arguments:
  -h, --help            show this help message and exit
  -I INTERFACE, --interface INTERFACE
                        the network interface to use for ping. pass the source IP on Windows
  -H PING_HOST, --ping-host PING_HOST
                        the host to ping (defaults to google.com)
  --ping-count PING_COUNT
                        how many ping health checks to perform
  --ping-interval PING_INTERVAL
                        how long in seconds to wait between ping health checks
  -R, --reboot          skip health checks and immediately reboot gateway
  -r, --skip-reboot     skip rebooting gateway
  --skip-bands          skip check for connected 4g band
  --skip-5g-bands       skip check for connected 5g band
  --skip-ping           skip check for successful ping
  --skip-enbid          skip check for connected eNB ID
  --uptime UPTIME       how long the gateway must be up before considering a
                        reboot (defaults to 90 seconds)
  -4 {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}, --4g-band {B2,B4,B5,B12,B13,B25,B26,B41,B46,B48,B66,B71}
                        the 4g band(s) to check
  -5 {n41,n71}, --5g-band {n41,n71}
                        the 5g band(s) to check (defaults to n41)
  --enbid ENBID         check for a connection to a given eNB ID
  --print-config        output configuration settings
  --logfile LOGFILE     output file for logging
  --log-all             always write connection details to logfile
  --log-delta           write connection details to logfile on change
```

## Options

### Ping options
**Interface:** `-I --interface`
    Can be used to specify the network interface used by the ping command. Useful if T-Mobile Home Internet is not your default network interface: e.g., this is running on a dual WAN router. On Windows, pass the source IP address to use.

**Ping Host:** `-H --ping-host`
    Defaults to `google.com` - override if you'd like to ping an alternate host to determine internet connectivity. Must specify a host if flag is provided - you can simply omit the flag if you'd like to use the default google.com ping check.

**Ping Count:** `--ping-count`
    Defaults to `1` - override if you'd like to perform multiple ping checks before rebooting. Short-circuits if a successful ping is encountered. Will reboot if all fail.

**Ping Interval:** `--ping-interval`
    Defaults to `10` seconds - override if you'd like to use a different interval.

### Reboot options
**Reboot:** `-R --reboot`
    Skip health checks and immediately reboot gateway.

**Skip Reboot:** `-r --skip-reboot`
    Skip rebooting gateway.

**Skip Bands:** `--skip-bands`
    Skip check for connected 4g band.

**Skip 5g Bands:** `--skip-5g-bands`
    Skip check for connected 5g band.

**Skip Ping:** `--skip-ping`
    Skip check for successful ping.

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


## Roadmap

(Not yet implemented):
- Alternate connectivity checks
- systemd service configuration

## Tip
Run this script with either a cronjob or as a systemd service to implement periodic recurring T-Mobile Home Internet health checks with automatic rebooting.

## Dockerized version

### Usage

Start the docker container with:

* Your env file mapped to `/.env`.
* A crontab file mapped to `/crontab`.

### Example

Running the container as:

```sh
docker run -v /etc/localtime:/etc/localtime:ro -v $PWD/monitor.env:/.env:ro -v $PWD/monitor.crontab:/crontab:ro hugohh/tmo-monitor:latest
```

with the following crontab:

```
*/2 * * * * /tmo-monitor/tmo-monitor.py --skip-bands
1 4 * * * /tmo-monitor/tmo-monitor.py --skip-ping
```

will run a ping test every 2 minutes and a band test every day at 4:01am.
