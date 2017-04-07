#!/usr/bin/env python

from io import open
import re
import sys

from setuptools import setup, find_packages


def version():
    with open('pypot/_version.py') as f:
        return re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read()).group(1)


extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True

install_requires = ['numpy',
                    'pyserial>2.6',
                    'tornado',
                    'scipy',
                    'ikpy',
                    'bottle',
                    'poppy-creature>=2'  # Kept to avoid breaking old imports
                    ]

if sys.version_info < (2, 7):
    print("python version < 2.7 is not supported")
    sys.exit(1)

if sys.version_info < (3, 4):
    install_requires.append('enum34')


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
      author_email='pierre.rouanet@gmail.com',
      description='Python Library for Robot Control',
      long_description=open('README.md', encoding='utf-8').read(),
      url='https://github.com/poppy-project/pypot',
      license='GNU GENERAL PUBLIC LICENSE Version 3',

      classifiers=[
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 3",
          "Topic :: Scientific/Engineering", ],

      **extra
      )
