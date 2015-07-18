#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Licensed under the GNU General Public License, version 3.
# See the file http://www.gnu.org/licenses/gpl.txt
#

from pisi.actionsapi import get
from pisi.actionsapi import autotools
from pisi.actionsapi import pisitools
from pisi.actionsapi import cmaketools

def setup():
    pisitools.dosed("CMakeLists.txt", "usr/sbin", "usr/bin")
    pisitools.dosed("src", "PyString_", "PyUnicode_")
    pisitools.dosed("src", "PyUnicode_AsString", "PyUnicode_AsUTF8String")
    pisitools.dosed("src", "PyInt_", "PyLong_")
    cmaketools.configure("-DPYTHON_INCLUDE_DIR=/usr/include/python3.4m \
                          -DPYTHON_LIBRARY=/usr/lib/libpython3.4m.so")

def build():
    autotools.make("VERBOSE=1")

def install():
    autotools.rawInstall("DESTDIR=%s" % get.installDIR())
    pisitools.dodir("/var/db")
