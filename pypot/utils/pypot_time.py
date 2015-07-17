import time as system_time


def time():
    return system_time.time()


def sleep(t):
    if t > 10:
        print('WARNING: big sleep', t)
        t = 0.1
    system_time.sleep(t)
