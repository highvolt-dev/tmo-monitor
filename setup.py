from setuptools import setup

setup(
  name='tmo_monitor',
  version='2.0.0-beta4',
  description='A script to monitor the T-Mobile Home Internet 5G Gateways',
  long_description='A lightweight, cross-platform Python 3 script that can monitor the T-Mobile Home Internet Arcadyan and Nokia 5G Gateways for 4G/5G bands, cellular site (tower), and internet connectivity and reboots as needed or on-demand.',
  url='https://github.com/highvolt-dev/tmo-monitor',
  author='highvolt-dev',
  license='MIT',
  packages=[
    'tmo_monitor',
    'tmo_monitor.gateway'
  ],
  scripts=['bin/tmo-monitor.py'],
  install_requires=[
    'parse',
    'python-dotenv',
    'requests',
    'tailer'
  ]
)
