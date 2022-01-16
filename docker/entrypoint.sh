#!/bin/sh -e

crontab -u monitor /crontab
crond -f
