#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
from pweb import __version__

setup(name='pweb',
      version=__version__,
      description='Python web Framework',
      author='Huaqing Ye',
      author_email='yhq1978@yahoo.com',
      url='http://pweb.takecar.cn/',
      scripts = ['scripts/pweb-admin.py'],
      packages=['pweb', 
                'pweb.conf', 
                'pweb.db',
                'pweb.handlers',
                'pweb.http',
                'pweb.middleware',
                'pweb.template',
                'pweb.utils'
               ],
      package_data = {'pweb':[
                            'examples/*.*',
                            'examples/index/*.*',
                            'examples/media/*.*',
                            'examples/templates/*.*',
                            ]},
      long_description="Think using pweb Framework.",
      license="Public domain",
      platforms=["any"],
     )