#!/usr/bin/env python

import re

from setuptools import setup, find_packages


def version():
  with open('pypot/_version.py') as f:
    return re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read()).group(1)


setup(name='pypot',
      version=version(),
      packages=find_packages(),

      install_requires=['numpy', 'pyserial'],

      extras_require={
        'tools': [], # Extras require: PyQt4 (not a PyPi packet)
        'doc': ['sphinx', 'sphinx-bootstrap-theme'],
        'server': ['bottle', 'tornado', 'zmq']
      },

      entry_points={
        'gui_scripts': [
                      'herborist = pypot.tools.herborist.herborist:main [tools]',
                      ],
      },

      setup_requires = ['setuptools_git >= 0.3',],

      include_package_data=True,
      exclude_package_data={'': ['README', '.gitignore']},

      zip_safe=True,

      author='Pierre Rouanet, Matthieu Lapeyre, Haylee Fogg',
      author_email='pierre.rouanet@gmail.com',
      description='Python Library for Robot Control',
      url='https://bitbucket.org/pierrerouanet/pypot',
      license='GNU GENERAL PUBLIC LICENSE Version 3'
      )
