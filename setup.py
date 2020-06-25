#!/usr/bin/env python

from io import open
import re
import os
import sys

from setuptools import setup, find_packages


def version():
    with open('pypot/_version.py') as f:
        return re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read()).group(1)

install_requires = ['numpy',
                    'pyserial>2.6',
                    'tornado',
                    'scipy',
                    'ikpy==3.0.1',
                    'bottle',
                    'requests',
                    'opencv-contrib-python',
                    'wget',
                    ]

if sys.version_info < (3, 5):
    print("python version < 3.5 is not supported")
    sys.exit(1)

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(path, filename)
            paths.append((path, [full_path]))
    return paths


setup(name='pypot',
      version=version(),
      packages=find_packages(),

      install_requires=install_requires,

      extras_require={
          'doc': ['sphinx', 'sphinxjp.themes.basicstrap', 'sphinx-bootstrap-theme'],
          'zmq-server': ['zmq'],
          'remote-robot': ['zerorpc'],
          'camera': ['hampy', 'zmq'],  # Extras require: opencv (not a PyPi packet)
          'tests': ['requests', 'websocket-client', 'poppy-ergo-jr'],
      },

      entry_points={
          'console_scripts': [
              'dxl-config = pypot.tools.dxlconfig:main',
              'poppy-services=pypot.creatures.services_launcher:main',
              'poppy-configure=pypot.creatures.configure_utility:main',
          ],
      },

      include_package_data=True,
      exclude_package_data={'': ['.gitignore']},

      zip_safe=False,

      author='See https://github.com/poppy-project/pypot/graphs/contributors',
      author_email='dev@poppy-station.org',
      description='Python 3 Library for Robot Control',
      long_description=open('README.md', encoding='utf-8').read(),
      url='https://github.com/poppy-project/pypot',
      license='GNU GENERAL PUBLIC LICENSE Version 3',

      classifiers=[
          "Programming Language :: Python :: 3",
          "Topic :: Scientific/Engineering", ],
      )
