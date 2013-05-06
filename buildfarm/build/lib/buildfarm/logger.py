#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Please read the COPYING file.
#

import os
import sys
import time

from buildfarm.config import configuration as conf

def find_caller():
    if os.path.splitext(__file__)[1] in [".pyc", ".pyo"]:
        src_file = "%s.py" % os.path.splitext(__file__)[0]
    else:
        src_file = __file__
    src_file = os.path.normcase(src_file)

    f = sys._getframe().f_back
    while True:
        code = f.f_code
        filename = os.path.normcase(code.co_filename)
        if filename == src_file:
            f = f.f_back
            continue
        return ":".join([os.path.basename(filename), str(f.f_lineno)])


def __raw(msg):
    open(conf.logfile, "a").write("\n\n%s\n\n" %(msg))

def __log(level, caller, msg):
    print msg
    open(conf.logfile, "a").write("%s | %-6.6s | %-16.16s :: %s\n" %(time.asctime(), level, caller, msg))


def debug(msg):
    __log("DEBUG", find_caller(), msg)

def error(msg):
    __log("ERROR", find_caller(), msg)

def info(msg):
    __log("INFO", find_caller(), msg)

def raw(msg = "-- --"):
    __raw(msg)
