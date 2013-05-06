#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.

import os
import sys
import glob
import shutil

from distutils.core import setup

import buildfarm

# tools to install under /usr/bin
TOOLS = glob.glob("tools/*")
HOOKS = glob.glob("hooks/*")

# Call distutils.setup

setup(name="buildfarm",
      version=buildfarm.__version__,
      description="Pisi Linux Buildfarm",
      long_description="A buildfarm framework which builds source packages for Pisi Linux",
      author="Ozan Çağlayan",
      author_email="ozan@pardus.org.tr",
      url="http://github.com/pisilinux",
      license="GPLv2",
      platforms=["Linux"],
      packages=["buildfarm"],
      scripts=TOOLS,
      data_files=[("/etc/buildfarm", ["data/buildfarm.conf", "data/auth.conf"]),
                   ("/etc/buildfarm/hooks.d", HOOKS)])
