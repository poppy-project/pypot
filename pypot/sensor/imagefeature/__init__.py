try:
    from .marker import MarkerDetector
except ImportError:
    pass

try:
    from .blob import BlobDetector
except ImportError:
    pass

try:
    from .face import FaceDetector
except ImportError:
    pass
