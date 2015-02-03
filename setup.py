#!/usr/bin/env python3
import os, shutil
from distutils.core import setup

shutil.copyfile('mario.py', 'mario')

setup(
        name = 'mario',
        version = '0.1',
        author = 'Damir Jelić',
        author_email = 'poljar[at]termina.org.uk',
        description = ('A simple plumber'),
        license = 'ISC',
        scripts = ['mario'],
      )

try:
    os.remove('mario')
except Exception:
    pass
