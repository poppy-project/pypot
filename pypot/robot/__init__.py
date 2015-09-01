from .robot import Robot
from .config import from_config, from_json, use_dummy_robot

try:
    from .remote import from_remote
except ImportError:
    pass

try:
    from ..vrep import from_vrep
except (ImportError, OSError):
    pass
