#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import sys
import os
import re
from optparse import OptionParser
from pisi.specfile import SpecFile

RELEASE = """\
        <Update release="%(RELEASE)s">
            <Date>%(DATE)s</Date>
            <Version>%(VERSION)s</Version>
            <Comment>Version bump.</Comment>
            <Name>%(NAME)s</Name>
            <Email>%(EMAIL)s</Email>
        </Update>"""

def get_and_save_user_info():
    info = [("NAME", "Please enter your full name as seen in pspec files"),
            ("EMAIL", "Please enter your e-mail as seen in pspec files")]
    res = {}
    conf_file = os.path.expanduser("~/.packagerinfo")
    if not os.path.exists(conf_file): open(conf_file, "a") 
    for line in open(conf_file, "r"):
        line = line.strip().split("=")
        try:
            res[line[0].strip()] = line[1].strip()
        except IndexError:
            pass
    for i in info:
        if not res.has_key(i[0]) or not res[i[0]]:
            print "%s is not defined in %s. %s" % (i[0], conf_file, i[1])
            res[i[0]] = raw_input("> ")
            open(conf_file, "a").write("%s\t= %s\n" % (i[0], res[i[0]]))
    return res

if __name__ == "__main__":
    ver_ext_pattern = re.compile("^.+?-[\D^\-]*?([\d\.]+\d)[\D^\.]*?\.([\w\.]+)$")
    types = ["targz", "tarbz2", "tarlzma", "tarxz", "tarZ", "tar", "zip", "gz", "gzip", "bz2", "bzip2", "lzma", "xz"]

    usage = "Usage: %prog [options] [PATH]"
    parser = OptionParser(usage)
    parser.add_option("-u", "--new-uri", dest="uri", help="version bump using specified uri")
    parser.add_option("-v", "--new-version", dest="ver", help="version bump using specified version")
    (options, args) = parser.parse_args()
    try:
        path = args[0]
    except IndexError:
        path = "."

    if path.endswith("/"): path = path[:-1]
    if not path.endswith("/pspec.xml"): path += "/pspec.xml"
    
    if not os.path.isfile(path):
        print "%s not found!" % path
        sys.exit(1)
    if not os.access(path, os.W_OK):
        print "Cannot write to %s." % path
        sys.exit(1)

    info = get_and_save_user_info()

    pspec = open(path, "r").read().strip()
    specfile = SpecFile(path)

    old_archive = specfile.source.archive 
    if len(old_archive) == 0:
        print("No <Archive> found in %s." % path)
        sys.exit(1)
    elif len(old_archive) > 1:
        print("Multiarchive pspec.xml not supported yet.")
        sys.exit(1)
    old_archive = old_archive[0].uri
    old_type = re.sub(ver_ext_pattern, "\\2", old_archive).replace(".", "")
    new_type = old_type

    if not options.uri and not options.ver:
        print old_archive
        sys.exit(0)

    last = specfile.history[0]
    old_version = last.version

    if options.uri and options.ver:
        print "Using options -u and -v together not allowed"
        sys.exit(1)
    elif options.uri:
        if not options.uri.split(":")[0] in ["ftp", "file", "http", "https", "mirrors"]:
            print "Wrong uri: %s" % options.uri
            sys.exit(1)
        new_archive = options.uri
        new_version = re.sub(ver_ext_pattern, "\\1", new_archive)
        new_type = re.sub(ver_ext_pattern, "\\2", new_archive).replace(".", "")
    elif options.ver:
        if not re.search("[\d\.]", options.ver):
            print "Wrong version number: %s" % options.ver
            sys.exit(1)
        new_version = options.ver
        new_archive = old_archive.replace(old_version, new_version)
    
    info["RELEASE"] = int(last.release) + 1
    info["DATE"] = time.strftime("%Y-%m-%d")
    info["VERSION"] = new_version
    new_release = RELEASE % info
    new_pspec = ''
    if not new_type in types: new_type = "binary"

    for line in pspec.split("\n"):
        if "<Archive" in line:
            new_line = line.split('>')
            new_line = new_line[0] + '>' + new_archive + '<' + new_line[1].split('<')[1] + '>'
            new_pspec = "\n".join((new_pspec, new_line))
        elif "<History>" in line:
            new_pspec = "\n".join((new_pspec, "    <History>\n%s" % new_release))
        else: 
            if not new_pspec: new_pspec = line
            else: new_pspec = "\n".join((new_pspec, line))

    open(path, "w").write(new_pspec)
    open(path, "a").write("\n")

    if os.getenv("USER") != "root":
        os.system("sudo pisi build %s --fetch" % path)
    else:
        os.system("pisi build %s --fetch" % path)

    sha1sum = os.popen("sha1sum /var/cache/pisi/archives/%s" % os.path.basename(new_archive)).read().split()[0]
    pspec = open(path, "r").read().strip()
    new_pspec = ''
    for line in pspec.split("\n"):
        if "<Archive" in line:
            new_line = re.sub("(.*sha1sum=)[\"\'][^\"^\']+[\"\'](.*)", r'\1"%s"\2' % sha1sum, line)
            new_line = re.sub("(.*type=)[\"\'][^\"^\']+[\"\'](.*)", r'\1"%s"\2' % new_type, line)
            new_pspec = "\n".join((new_pspec, new_line))
        else: 
            if not new_pspec: new_pspec = line
            else: new_pspec = "\n".join((new_pspec, line))

    open(path, "w").write(new_pspec)
    open(path, "a").write("\n")
