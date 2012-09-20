import unittest
import random

import pypot.dynamixel.conversions as conv


class TestConversion(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_position_degree(self):        
        for model in conv.position_range.keys():
            pmax, dmax = conv.position_range[model]
            
            # Test position to degree
            self.assertEqual(conv.position_to_degree(0, model), -dmax / 2)
            self.assertEqual(conv.position_to_degree(pmax -1, model), dmax / 2)
            

            self.assertTrue(abs(conv.position_to_degree(pmax / 2, model) - 0) < 0.2)
            
            return
            
            for _ in range(10):
                N = random.randint(1, 100)
                self.assertAlmostEqual(conv.position_to_degree(conv.position_range[model][0] / N, model),
                                       conv.position_range[model][1] / N,
                                       places=0)
            
            
            x = random.randint(conv.position_range[model][0] + 1, conv.position_range[model][0] + 100)
            self.assertRaises(ValueError, conv.position_to_degree, x, model)
            
            x = random.randint(-100, -1)
            self.assertRaises(ValueError, conv.position_to_degree, x, model)
            
            # Test degree to position
            self.assertEqual(conv.degree_to_position(0, model), 0)
            
            self.assertEqual(conv.degree_to_position(conv.position_range[model][1], model),
                             conv.position_range[model][0])
            
            for _ in range(10):
                N = random.randint(1, 100)
                self.assertAlmostEqual(conv.degree_to_position(conv.position_range[model][1] / N, model),
                                       conv.position_range[model][0] / N,
                                       places=0)
            
            
            x = random.randint(conv.position_range[model][1] + 1,
                               conv.position_range[model][1] + 100)
            self.assertRaises(ValueError, conv.degree_to_position, x, model)
            
            x = random.randint(-100, -1)
            self.assertRaises(ValueError, conv.degree_to_position, x, model)
        
        
        for _ in range(10):
            model = random.choice(conv.position_range.keys())
            x = random.randint(0, conv.position_range[model][1])
            
            self.assertAlmostEqual(x,
                                   conv.position_to_degree(conv.degree_to_position(x, model), model),
                                   places=0)
    
    
    def test_speed_rpm(self):
        # Test speed to rpm
        self.assertEqual(conv.speed_to_rpm(0), 0)
        self.assertEqual(conv.speed_to_rpm(conv.SPEED_MAX / 2), 0)

        self.assertAlmostEqual(conv.speed_to_rpm(conv.SPEED_MAX - 1),
                               conv.RPM_MAX,
                               places=2)

        self.assertAlmostEqual(conv.speed_to_rpm((conv.SPEED_MAX / 2) - 1),
                               -conv.RPM_MAX,
                               places=2)
        
        
        for _ in range(10):
            s = random.randint(0, (conv.SPEED_MAX / 2) - 1)
            
            err = abs(conv.speed_to_rpm(s) - (-conv.RPM_MAX * (float(s) / ((conv.SPEED_MAX / 2) - 1))))
            self.assertTrue(err < 1)
        
            err = abs(conv.speed_to_rpm(s + conv.SPEED_MAX / 2) - (conv.RPM_MAX * (float(s) / ((conv.SPEED_MAX / 2) - 1))))
            self.assertTrue(err < 1)
                
        
        for _ in range(10):
            x = random.randint(0, (conv.SPEED_MAX / 2) - 1)
            self.assertEqual(conv.speed_to_rpm(x),
                             -conv.speed_to_rpm(x + conv.SPEED_MAX / 2))
                
        
        
        x = random.randint(conv.SPEED_MAX + 1, conv.SPEED_MAX + 100)
        self.assertRaises(ValueError, conv.speed_to_rpm, x)
        
        x = random.randint(-100, -1)
        self.assertRaises(ValueError, conv.speed_to_rpm, x)
        
        # Test rpm to speed
        self.assertEqual(conv.rpm_to_speed(0), 0)
        self.assertTrue(abs(conv.rpm_to_speed(conv.RPM_MAX) - conv.SPEED_MAX) <= 1)
        
        for _ in range(10):
            r = random.randint(0, int(conv.RPM_MAX))
                
            err = abs(conv.rpm_to_speed(r) - ((conv.SPEED_MAX / 2) + (r / conv.RPM_MAX) * ((conv.SPEED_MAX / 2) - 1)))
            self.assertTrue(err < 1)
            
            err = abs(conv.rpm_to_speed(-r) - (r / conv.RPM_MAX) * ((conv.SPEED_MAX / 2) - 1))
            self.assertTrue(err < 1)


        x = random.randint(int(conv.RPM_MAX) + 1, int(conv.RPM_MAX) + 100)
        self.assertRaises(ValueError, conv.rpm_to_speed, x)
        self.assertRaises(ValueError, conv.rpm_to_speed, -x)
        
        for _ in range(10):
            x = random.randint(0, conv.SPEED_MAX - 1)
            err = abs(x - conv.rpm_to_speed(conv.speed_to_rpm(x)))
            self.assertTrue(err < 1)    
    
    def test_load_to_percent(self):        
        self.assertEqual(0, conv.load_to_percent(0))
        self.assertEqual(0, conv.load_to_percent(conv.LOAD_MAX / 2))
        
        self.assertEqual(100, conv.load_to_percent(conv.LOAD_MAX - 1))
        self.assertEqual(-100, conv.load_to_percent((conv.LOAD_MAX / 2) - 1))
                
        x = random.randint(1, 100)
        self.assertRaises(ValueError, conv.load_to_percent, -x)
        self.assertRaises(ValueError, conv.load_to_percent, conv.LOAD_MAX + x)
        
        for _ in range(10):
            N = random.randint(1, 100)
            x = (N / 100.0) * ((conv.LOAD_MAX / 2) - 1)
            
            err = abs(N - (-conv.load_to_percent(x)))
            self.assertTrue(err < 1)
            
            err = abs(N - (conv.load_to_percent(conv.LOAD_MAX / 2 + x)))
            self.assertTrue(err < 1)
    
    
    def test_percent_to_torque(self):
        self.assertEqual(conv.percent_to_torque_limit(0), 0)
        self.assertEqual(conv.percent_to_torque_limit(100), conv.MAX_TORQUE)
        
        x = random.randint(1, 100)
        self.assertRaises(ValueError, conv.percent_to_torque_limit, -x)
        self.assertRaises(ValueError, conv.percent_to_torque_limit, 100 + x)
        
        for _ in range(10):
            N = random.randint(1, 100)
            
            err = abs(conv.percent_to_torque_limit(100.0 / N) - (float(conv.MAX_TORQUE) / N))
            self.assertTrue(err <= 0.5)
    
    def test_integer_to_bytes(self):
        self.assertEqual((0, 0), conv.integer_to_two_bytes(0))
        self.assertEqual((0, 1), conv.integer_to_two_bytes(256))
        
        self.assertEqual(conv.two_bytes_to_integer((0, 0)), 0)
        self.assertEqual(conv.two_bytes_to_integer((0, 1)), 256)
        
        for _ in range(10):
            x = random.randint(0, 65535)
            self.assertEqual(x,
                             conv.two_bytes_to_integer(conv.integer_to_two_bytes(x)))


if __name__ == '__main__':
    unittest.main()
