#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name="i3pystatus",
      version="3.35",
      description="A complete replacement for i3status",
      url="http://github.com/enkore/i3pystatus",
      license="MIT",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: X11 Applications",
          "License :: OSI Approved :: MIT License",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python :: 3",
          "Topic :: Desktop Environment :: Window Managers",
      ],
      packages=find_packages(include=['i3pystatus', 'i3pystatus.*']),
      entry_points={
          "console_scripts": [
              "i3pystatus = i3pystatus:main",
              "i3pystatus-setting-util = i3pystatus.tools.setting_util:main"
          ]
      },
      zip_safe=True,
      )
