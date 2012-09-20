import unittest
import random

import pypot.dynamixel
import pypot.dynamixel.io as io


class TestConnnection(unittest.TestCase):
    
    def setUp(self):
        self.port = pypot.dynamixel.get_available_ports()[0]
    
    def tearDown(self):
        pass

    def test_port(self):
        self.assertEqual(pypot.dynamixel.get_available_ports(),
                         pypot.dynamixel.get_available_ports())

    
    def test_opening(self):
        dyn_io = io.DynamixelIO(self.port)

        self.assertRaises(IOError, io.DynamixelIO, '/dev/tty.bob')
    
    def test_multiple_opening(self):
        for _ in range(random.randint(2, 10)):
            dyn_io = io.DynamixelIO(self.port)
            del dyn_io

        dyn_io = io.DynamixelIO(self.port)
        self.assertRaises(IOError, io.DynamixelIO, self.port)


class TestDiscovery(unittest.TestCase):
    
    def setUp(self):
        port = pypot.dynamixel.get_available_ports()[0]
        self.dyn_io = io.DynamixelIO(port)

    def tearDown(self):
        pass

    def test_ping(self):
        mid = random.randint(255, 1000)
        self.assertRaises(ValueError, self.dyn_io.ping, mid)
        mid = random.randint(0, 253)
        self.assertRaises(ValueError, self.dyn_io.ping, -mid)

        
        motor_ids = self.dyn_io.scan(range(25))
        for mid in motor_ids:
            self.assertTrue(self.dyn_io.ping(mid))

        while True:
            mid = random.randint(0, 253)
            if mid not in motor_ids:
                break

        self.assertFalse(self.dyn_io.ping(mid))


if __name__ == '__main__':
    unittest.main()