import os
import random
import unittest

from setuptools import find_packages


class TestImport(unittest.TestCase):
    def setUp(self):
        self.packages = find_packages('../')

        if os.uname()[-1].startswith('arm'):
            self.packages = [p for p in self.packages
                             if not p.startswith('pypot.vrep')]

        random.shuffle(self.packages)

    def test_import(self):
        [__import__(package) for package in self.packages]


if __name__ == '__main__':
    unittest.main()
