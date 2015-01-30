import cv2
import logging

from ..utils.stoppablethread import StoppableLoopThread


logger = logging.getLogger(__name__)


class Camera(StoppableLoopThread):
    def __init__(self, camera_id=-1, fps=25, resolution=[320, 240]):
        StoppableLoopThread.__init__(self, fps)

        self.capture = cv2.VideoCapture(camera_id)
        # This should work but it does not ...
        # self.capture.set(cv2.cv.CV_CAP_PROP_CONVERT_RGB, True)
        self.resolution = resolution
        self.fps = fps

        # try to get a first frame
        if not self.capture.isOpened():
            raise ValueError('Can not open camera device {}'.format(camera_id))

        self.rval, frame = self.capture.read()
        if not self.rval:
            raise EnvironmentError('Can not grab an image from the camera device')

        self._last_frame = None

        self.start()  # Autostart

    def __del__(self):
        self.capture.release()

    def update(self):
        self.rval, img = self.capture.read()
        if self.rval:
            self._last_frame = img

    @property
    def last_frame(self):
        """ Directly returns the last grabbed frame. """
        return self.post_processing(self._last_frame)

    def post_processing(self, img):
        """ Returns the image post processed. """
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @property
    def resolution(self):
        return [self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH),
                self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)]

    @resolution.setter
    def resolution(self, new_resolution):
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, new_resolution[0])
        self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, new_resolution[1])

    @property
    def fps(self):
        return self.capture.get(cv2.cv.CV_CAP_PROP_FPS)

    @fps.setter
    def fps(self, new_fps):
        ischanged = self.capture.set(cv2.cv.CV_CAP_PROP_FPS, new_fps)

        if not ischanged:
            logger.warning('Cannot set the camera fps to {} (current: {})!'.format(new_fps, self.fps))

        self.period = 1.0 / new_fps
