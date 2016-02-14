#!/usr/bin/env python

from setuptools import setup

setup(name="i3pystatus",
      version="3.34",
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
      packages=[
          "i3pystatus",
          "i3pystatus.core",
          "i3pystatus.tools",
          "i3pystatus.mail",
          "i3pystatus.pulseaudio",
          "i3pystatus.updates",
      ],
      entry_points={
          "console_scripts": [
              "i3pystatus = i3pystatus:main",
              "i3pystatus-setting-util = i3pystatus.tools.setting_util:main"
          ]
      },
      zip_safe=True,
      )
