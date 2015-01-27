#!/usr/bin/env python

import re
import sys

from setuptools import setup, find_packages


def version():
    with open('pypot/_version.py') as f:
        return re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read()).group(1)

extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True

setup(name='pypot',
      version=version(),
      packages=find_packages(),

      install_requires=['numpy', 'pyserial'],

      extras_require={
          'tools': [],  # Extras require: PyQt4 (not a PyPi packet)
          'doc': ['sphinx', 'sphinx-bootstrap-theme'],
          'server': ['bottle', 'tornado', 'pyzmq'],
          'remote-robot': ['zerorpc'],
          'square-signal': ['scipy']
      },

      entry_points={
          'gui_scripts': [
              'herborist = pypot.tools.herborist.herborist:main [tools]',
          ],
      },

      setup_requires=['setuptools_git >= 0.3', ],

      include_package_data=True,
      exclude_package_data={'': ['README', '.gitignore']},

      zip_safe=False,

      author='Pierre Rouanet, Steve N\'Guyen, Matthieu Lapeyre',
      author_email='pierre.rouanet@gmail.com',
      description='Python Library for Robot Control',
      url='https://github.com/poppy-project/pypot',
      license='GNU GENERAL PUBLIC LICENSE Version 3',

      classifiers=[
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 3",
          "Topic :: Scientific/Engineering", ],

      **extra
      )
