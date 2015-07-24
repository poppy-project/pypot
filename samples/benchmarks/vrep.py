import os
import json
import time

import pypot
import poppytools

from pypot.vrep import from_vrep
from pypot.primitive import LoopPrimitive


if __name__ == '__main__':
    DT = 30.

    class JustWaitingPrimitive(LoopPrimitive):
        def update(self):
            if self.elapsed_time > DT:
                self.stop(wait=False)

    configfile = os.path.join(os.path.dirname(poppytools.__file__),
                              'configuration', 'poppy_config.json')

    with open(configfile) as f:
        poppy_config = json.load(f)

    scene_path = os.path.join(os.path.dirname(pypot.__file__),
                              '..', 'samples', 'notebooks', 'poppy-sitting.ttt')

    poppy = from_vrep(poppy_config, '127.0.0.1', 19997, scene_path)

    time.sleep(0.1)

    p = JustWaitingPrimitive(poppy, 50.)

    t0 = time.time()
    p.start()
    p.wait_to_stop()
    print('Running {}s of v-rep simulation took {}s'.format(DT, time.time() - t0))
