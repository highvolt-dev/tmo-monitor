from enum import Enum

class ExitStatus(Enum):
  GENERAL_ERROR = 1
  CONFIGURATION_ERROR = 2
  API_ERROR = 3
  REBOOT_PERFORMED = 4
