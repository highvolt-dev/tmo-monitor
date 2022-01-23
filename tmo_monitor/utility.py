import logging

def print_and_log(msg, level='INFO'):
  print(msg)
  lvl = logging.getLevelName(level)
  if type(lvl) != int:
    lvl = 20 # Set to INFO as default, Python bug between 3.4 to 3.42
  logging.log(lvl, msg)