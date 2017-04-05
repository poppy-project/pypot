from math import ceil
from collections import OrderedDict
import numpy as np
import bisect
import operator


class PositionsInterpolationDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        self.interpolation_kind = 'linear'
        super(OrderedDict).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super(OrderedDict).__setitem__(float(key), value)

    def _nearest_time_keys(self, key, number_of_keys=3):
        """ Find nearest keys on position timestamps with a dichotomy (bisect) algorithm """
        index_ref = bisect.bisect_left(list(self), key)
        #
        # if number_of_keys=3 indexes=[index - 1, index, index + 1]
        time_keys = []
        for i in range(number_of_keys):
            if i % 2 == 0:
                tmp_index = index_ref + (-1) * ceil(i / 2)
            else:
                tmp_index = index_ref + ceil(i / 2)
            # Filter to avoid IndexError
            if tmp_index > len(self) - 1:
                tmp_index = len(self) - 1
            elif tmp_index < 0:
                tmp_index = 0
            time_keys.append(list(self)[tmp_index])
        return sorted(time_keys)

    def _interpolate_timed_positions(self, input_time_key):
        """ Return a dict of position and speed (linear) interpolated for each motor at the given time frame key. """
        nearest_time_keys = self._nearest_time_keys(input_time_key)
        print("_interpolate_timed_positions", nearest_time_keys, input_time_key)
        interpolated_positions = {}
        x = np.array(nearest_time_keys)

        # Loop on the smaller motor id list: allow interpolation on Movements with
        # non consistent tracked motors
        for motor in min([list(self[tkey]) for tkey in nearest_time_keys], key=operator.itemgetter(1)):
            y_pos = np.array([self[tk][motor][0] for tk in nearest_time_keys])
            y_speed = np.array([self[tk][motor][1] for tk in nearest_time_keys])
            interpolated_positions[motor] = (
                np.interp(input_time_key, x, y_pos), np.interp(input_time_key, x, y_speed))

        return interpolated_positions

    def __missing__(self, key):
        """ Return an interpolated positions dict if key is missing """
        if key is None:
            raise SyntaxError('invalid syntax, you must provide a key')
        return self._interpolate_timed_positions(key)
