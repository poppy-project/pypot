import time as system_time

def time():
    # print "CUSTOM TIME"
    return system_time.time()

def sleep(t):
    # print "CUSTOM SLEEP"
    system_time.sleep(t)
