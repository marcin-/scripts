#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import pisi
import sys
import os
from optparse import OptionParser

RELEASE = """\
        <Update release="%s">
            <Date>%s</Date>
            <Version>%s</Version>
            <Comment>%s</Comment>
            <Name>%s</Name>
            <Email>%s</Email>
        </Update>"""

spec_file = "pspec.xml"

def get_and_save_user_info():
    name = "PACKAGER_NAME"
    email = "PACKAGER_EMAIL"
    root = "PATH_TO_SRC_REPO"

    conf_file = os.path.expanduser("~/.packagerinfo")
    if os.path.exists(conf_file):
        # Read from it
        name, email, root = open(conf_file, "r").read().strip().split(",")

    else:
        print "Please enter your full name as seen in pspec files"
        name = raw_input("> ")
        print "Please enter your e-mail as seen in pspec files"
        email = raw_input("> ")
        print "Please enter path to to your src repo"
        root = raw_input("> ")
        while root.endswith("/"): root = root[:-1]

        print "Saving packager info into %s" % conf_file
        open(conf_file, "w").write("%s,%s,%s" % (name, email, root))

    return name, email, root

def update_pspec(path, comment):
    pspec = open(path, "r").read().strip()
    last = pisi.specfile.SpecFile(path).history[0]
    release = int(last.release) + 1
    date = time.strftime("%Y-%m-%d")
    new_release = RELEASE % (release, date, last.version, comment, packager_name, packager_email)
    new_pspec = ''
    if len(pisi.specfile.SpecFile(path).source.archive) == 0:
        print("No <Archive> found in %s." % path)
        sys.exit(1)
    for line in pspec.split("\n"):
        if "<History>" in line:
            new_pspec = "\n".join((new_pspec, "    <History>\n%s" % new_release))
        else: 
            if not new_pspec: new_pspec = line
            else: new_pspec = "\n".join((new_pspec, line))
    return new_pspec

if __name__ == "__main__":
    usage = "Usage: %prog [comment]"
    parser = OptionParser(usage)
    (options,args) = parser.parse_args()
    try:
        comment = args[0]
    except IndexError:
        print "You should write a comment!"
        sys.exit(1)

    packager_name, packager_email, src_root = get_and_save_user_info()

    path_to_pspec = ""
    for root, dirs, files in os.walk(src_root):
        for d in dirs:
            path_to_pspec = "%s/%s/%s" % (root, d, spec_file)
            if not os.path.exists(path_to_pspec): continue
            elif not os.access(path_to_pspec, os.W_OK):
                print "Cannot write to %s" % path_to_pspec
                continue
            print "Updating: %s" % path_to_pspec
            pspec = update_pspec(path_to_pspec, comment)
            open(path_to_pspec, "w").write(pspec)
            open(path_to_pspec, "a").write("\n")
