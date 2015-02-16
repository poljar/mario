#!/usr/bin/env python3
import os, shutil
from setuptools import setup
from xdg import BaseDirectory

setup(name = 'mario',
      version = '0.1',
      author = 'Damir Jelić, Denis Kasak',
      author_email = 'poljar[at]termina.org.uk, dkasak[at]termina.org.uk',
      description = ('A simple plumber'),
      install_requires = ['python-magic', 'pyxdg'],
      license = 'ISC',
      entry_points = {
          "console_scripts" : ['mario = mario:main']
          }
     )
