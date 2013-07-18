#!/usr/bin/env python

from setuptools import setup

setup(name="i3pystatus",
      version="3.16",
      description="Like i3status, this generates status line for i3bar / i3wm",
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

      packages=[
        "i3pystatus",
        "i3pystatus.core",
        "i3pystatus.core.threading",
        "i3pystatus.mail"
      ],
      entry_points={
        "console_scripts": ["i3pystatus = i3pystatus:main"],
      },
     )
