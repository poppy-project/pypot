from .robot import Robot
from .config import from_config, from_json

try:
    from .remote import from_remote
except ImportError:
    pass

from ..vrep import from_vrep
