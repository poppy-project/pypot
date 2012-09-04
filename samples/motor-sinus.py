# coding=utf-8

import os
import sys
import time

import numpy

sys.path.append(os.path.join(os.getcwd(), '..'))

import pypot.dynamixel



timeout = 1

if __name__ == '__main__':
    ports = pypot.dynamixel.get_available_ports()
    if not ports:
        print 'No port found :-('
        sys.exit(1)

    port = ports[0]
    print 'Try to connect on ', port
    dxl_io = pypot.dynamixel.DynamixelIO(port, timeout=timeout)
    
    print 'Connexion established :', dxl_io
    
    motor_ids = dxl_io.scan(range(25))
    print len(motor_ids), 'motors found:', motor_ids
    
    print 'Model'
    print [dxl_io.get_model(mid) for mid in motor_ids]
    
    print 'Return delay time'
    print [dxl_io.get_return_delay_time(mid) for mid in motor_ids]
    
    
    print 'Setting the position of all motors to the origin'
    origin = 150.0
    dxl_io.set_sync_positions(zip(motor_ids, [origin] * len(motor_ids)))
    time.sleep(1)
    
    positions = numpy.sin(numpy.arange(0, 2 * numpy.pi, 0.01))
    amp = 100.0
    i = 0
    
    dt = []
    while True:
        t1 = time.time()
        #values = dxl_io.get_sync_positions_speeds_loads(motor_ids)
        for mid in motor_ids:
            dxl_io.get_position_speed_load(mid)
        t2 = time.time()
        dt.append((t2 - t1) * 1000)
        
        pos = origin + amp * positions[i]
        dxl_io.set_sync_positions(zip(motor_ids, [pos] * len(motor_ids)))
        
        time.sleep(0.05)
        
        i += 1
        if i >= len(positions):
            i = 0
            print numpy.mean(dt), numpy.std(dt)
            dt = []