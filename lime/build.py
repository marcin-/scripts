#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Licensed under the GNU General Public License, version 3.
# See the file http://www.gnu.org/licenses/gpl.txt

#from lime.buildapi import get
from lime.buildapi import autotools
#from lime.buildapi import limetools

pkgname="attr"
pkgver="2.4.47"
pkgrel=4
pkgdesc="Utilities for managing filesystems extended attributes"
url="http://acl.bestbits.at"
arch="all"
license="GPL2+ LGPL2+"
depends=""
makedepends="libtool autoconf automake bash gzip"
subpackages=f"{pkgname}-dev {pkgname}-doc libattr" #python3.6
source="http://download.savannah.gnu.org/releases-noredirect/attr/attr-2.4.47.src.tar.gz \
    some.patch \
    "

def setup():
    autotools.rawConfigure("--libdir=/lib \
                            --mandir=/usr/share/man \
                            --libexecdir=/lib \
                            --bindir=/usr/bin")
#def build():
#    autotools.make()

#def package():
#    autotools.make("DIST_ROOT=%s install install-lib install-dev" % get.installDIR())

#    limetools.subpackage("libattr")
#    limetools.libs() # for use default split libs operations