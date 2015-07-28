We generate the profile using [yappi](https://bitbucket.org/sumerc/yappi/) and export the stats using the pstat format. For instance,

```python

import time
import yappi

from poppy.creatures import PoppyErgoJr
jr = PoppyErgoJr()

yappi.start();time.sleep(100); yappi.stop()
yappi.get_func_stats().save('ergo-jr-rpi2-idle-light-syncloop.prof', type='pstat')

```

The stats can be visualized using [snakeviz](http://jiffyclub.github.io/snakeviz/?utm_content=buffer81a13&utm_medium=social&utm_source=twitter.com&utm_campaign=buffer).
