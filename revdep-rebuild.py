#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author: Marcin Bojara <marcin@pisilinux.org>

import os
import re
import sys
import glob
import hashlib
import subprocess
import pisi.context as ctx

from optparse import OptionParser
from pisi.db.installdb import InstallDB

CACHEDIR = "/var/cache/pisi/"
VRPATTERN = re.compile("(.*)-(\d+)$")
SOLIBPATTERN = re.compile("(.*?\.so[\.\d]*)$")
DOCPKGPATTERN = re.compile("(.*)-docs?$")
SEARCH_DIRS="/lib /bin /sbin /usr/lib /usr/bin /usr/sbin /usr/libexec /usr/local /usr/qt* /usr/kde/*/bin /usr/lib/MozillaFirefox /usr/kde/*/lib /usr/*-*-linux-gnu /opt".split()
EXCLUDE_DIRS="/opt/ptsp /usr/lib/xorg/nvidia* /usr/lib/debug".split()
LIST="%s/.revdep-rebuild" % os.environ["HOME"]

NO = "\x1b[0;0m"
BR = "\x1b[0;01m"
CY = "\x1b[36;01m"
GR = "\x1b[32;01m"
RD = "\x1b[31;01m"
YL = "\x1b[33;01m"
BL = "\x1b[34;01m"

if __name__ == "__main__":
    parser = OptionParser("Usage: %prog [options]")
    parser.add_option("-f", "--force", action="store_true", help="remove old revdep-rebuild files")
    parser.add_option("-n", "--soname", action="store_true", default=None, help="recompile packages using library with SONAME instead of broken library \
                                                                            (SONAME providing library must be present in the system)")
    parser.add_option("-e", "--soname-regexp", action="store_true", default=None, help="the same as --soname, but accepts regular expresions")
    (options, args) = parser.parse_args()

    glob_paths = []
    for path in SEARCH_DIRS:
        if "*" in path:
            glob_paths.extend(glob.glob(path))
    if glob_paths: SEARCH_DIRS.extend(glob_paths)
    SEARCH_DIRS = [p for p in SEARCH_DIRS if not "*" in p and os.path.isdir(p)]
    glob_paths = []
    for path in EXCLUDE_DIRS:
        if "*" in path:
            glob_paths.extend(glob.glob(path))
    if glob_paths: EXCLUDE_DIRS.extend(glob_paths)
    EXCLUDE_DIRS = [p for p in EXCLUDE_DIRS if not "*" in p]

    if options.force:
        for f in  glob.glob("%s/.revdep-rebuild*" % os.environ["HOME"]): os.remove(f)

    if not options.soname and not options.soname_regexp:
        search_broken = True
    elif options.soname and options.soname_regexp:
        print "%suse --soname and --soname-regexp separately%s" % (RD, NO)
        sys.exit(1)
    else:
        search_broken = False

    if search_broken:
        soname_search = ["not"]
        llist = LIST
        head_text = "broken by any package update"
        ok_text = "Dynamic linking on your system is consistent"
        working_text = " consistency"
    else:
        soname_search = sorted(args)
        sonames = " ".join(soname_search)
        m = hashlib.md5()
        m.update(sonames)
        llist = LIST + "_" + m.hexdigest()[:8]
        head_text = "using given shared object(s) name"
        ok_text = "There are no dynamic links to %s" % sonames
        working_text = ""

    print "\nChecking reverse dependencies..."

    print "\n%sCollecting system binaries and libraries...%s" % (GR, NO)

    if os.path.isfile("%s.1_files" % llist):
        print "  using existing %s.1_files." % llist
        with open("%s.1_files" % llist) as f:
            ffiles = [l.strip() for l in f.readlines()]
    else:
        ffiles = []
        for dir in SEARCH_DIRS:
            for root, dirs, files in os.walk(dir):
                if root in EXCLUDE_DIRS: continue
                for f in files:
                    path = os.path.join(root, f)
                    if os.access(path, os.X_OK) or re.search(SOLIBPATTERN, f):
                        ffiles.append(path)
        ffiles = sorted(ffiles)
        open("%s.1_files" % llist, "w").write("\n".join(ffiles))
    print "  done. (%s.1_files)" % llist

    if search_broken:
        print "\n%sCollecting complete LD_LIBRARY_PATH...%s" % (GR, NO)
        if os.path.isfile("%s.2_ldpath" % llist):
            print "  using existing %s.2_ldpath." % llist
            with open("%s.2_ldpath" % llist) as f:
                ldpaths = f.readline().split(":")
        else:
            ldpaths = []
            for f in ffiles:
                if re.search(SOLIBPATTERN, f) and not os.path.dirname(f) in ldpaths:
                    ldpaths.append(os.path.dirname(f))
            for f in os.listdir("/etc/ld.so.conf.d"):
                with open("/etc/ld.so.conf.d/%s" % f) as cf:
                    for line in [l.strip() for l in cf.readlines()]:
                        if line.startswith("/") and not line in ldpaths and os.path.isdir(line):
                            ldpaths.append(line)
            ldpaths = sorted(ldpaths)
            open("%s.2_ldpath" % llist, "w").write(":".join(ldpaths))
        os.environ["COMPLETE_LD_LIBRARY_PATH"] = ":".join(ldpaths)
        print "  done. (%s.2_ldpath)" % llist

    print "\n%sChecking dynamic linking%s...%s" % (GR, working_text, NO)

    if os.path.isfile("%s.3_rebuild" % llist):
        print "  using existing %s.3_rebuild." % llist
        with open("%s.3_rebuild" % llist) as f:
            rebuild = [l.strip() for l in f.readlines()]
    else:
        rebuild = []
        for f in ffiles:
            p = subprocess.Popen('LD_LIBRARY_PATH="$COMPLETE_LD_LIBRARY_PATH" ldd %s' % f, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            for line in out.split("\n"):
                if "=>" in line:
                    src, dst = line.split("=>")
                    src = src.strip()
                    dst = dst.split()[0].strip()
                    for pattern in soname_search:
                        if options.soname_regexp:
                            if re.search(pattern, dst):
                                print "  found %s" % f
                                rebuild.append("%s:%s" % (f, src))
                                break
                        else:
                            if pattern == dst:
                                rebuild.append("%s:%s" % (f, dst))
                                if search_broken:
                                    print "  broken %s requires %s" % (f, src)
                                else:
                                    print "  found %s" % f
        rebuild = sorted(rebuild)
        open("%s.3_rebuild" % llist, "w").write("\n".join(rebuild))
    print "  done. (%s.3_rebuild)" % llist

    print "\n%sDetermining package names%s...%s" % (GR, working_text, NO)

    installdb = InstallDB()
    idb = installdb.installed_db
    pkgfs = {}
    for pkg, vr in idb.iteritems():
        if re.search(DOCPKGPATTERN, pkg): continue
        ver = re.sub(VRPATTERN, "\\1", vr)
        files_xml = open(os.path.join(installdb.package_path(pkg), ctx.const.files_xml)).read()
        pkgfs[pkg] = re.compile('<Path>(.*?\.so[\.\d]*)</Path>', re.I).findall(files_xml)

    if os.path.isfile("%s.4_names" % llist):
        print "  using existing %s.4_names." % llist
        with open("%s.4_names" % llist) as f:
            names = [l.strip() for l in f.readlines()]
    else:
        names = []
        for f in rebuild:
            l, n = f.split(":")
            for pkg, fs in pkgfs.iteritems():
                if l[1:] in fs:
                    print "  %s has %s" % (pkg, l)
                    names.append("%s:%s" % (pkg, l))
            
        names = sorted(names)
        open("%s.4_names" % llist, "w").write("\n".join(names))
    print "  done. (%s.4_names)" % llist
