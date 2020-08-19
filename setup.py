#!/usr/bin/env python2.7
try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(name="wuutils",
      version="0.0.21",
      description="Dumb utility functions I use",
      license="MIT",
      author="Eugene Wu",
      author_email="ewu@cs.columbia.edu",
      url="http://github.com/sirrice/wuutils",
      packages = find_packages(),
      include_package_data = True,
      package_dir = {'wuutils' : 'wuutils'},
      install_requires = [
        'pygg',
        'sqlalchemy',
        'cashier',
        'pandas'
      ],
      keywords= "")
