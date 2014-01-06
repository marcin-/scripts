#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Pisilinux system for creation, deletion and cleaning of volatile and temporary files.
"""

import os
import re
import sys
import shutil

from pwd import getpwnam
from grp import getgrnam

DEFAULT_CONFIG_DIRS = ["/etc/tmpfiles.d", "/usr/lib/tmpfiles.d"]

def read_file(path):
    with open(path) as f:
        return f.read().strip()

def write_file(path, content, mode = "w"):
    open(path, mode).write(content)

def create(type, path, mode, uid, gid, age, arg):
    print type, path, mode, uid, gid, age, arg
    if not re.search("^\d{4}$", mode): mode="0755"
    mode = int(mode, 8)
    if not uid: uid = "root"
    if not gid: gid = "root"
    uid = getpwnam(uid).pw_uid
    gid = getgrnam(gid).gr_gid
    if type == "D":
        if os.path.isdir(path): shutil.rmtree(path)
        elif os.path.islink(path): os.remove(path)
    if type.lower() == "d":
        if not os.path.isdir(path): os.makedirs(path, mode)
        os.chown(path, uid, gid)
    elif type in ["f", "F", "w"]:
        if not os.path.isfile(path) and type == "w": return
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
            os.chown(os.path.dirname(path), uid, gid)
        write_file(path, arg, mode = "a" if type == "f" else "w")
        os.chown(path, uid, gid)

if __name__ == "__main__":
    def ewe(msg):
        print msg
        sys.exit(1)

    config_files = {}
    def add_config_file(head, tail):
        try:
            config_files[head].append(tail)
        except KeyError:
            config_files[head] = [tail]

    for arg in sys.argv[1:]:
        (head, tail) = os.path.split(arg)
        if not tail.endswith(".conf"): ewe("%s is not .conf file" % tail)
        elif not head: ewe("Full path is needed for %s args." % sys.argv[0])
        elif not os.path.isdir(head): ewe("Path %s not exists." % head)
        elif not os.path.isfile(arg): ewe("File %s not exists." % arg)
        add_config_file(head, tail)
    else:
        all_files_names = []
        for head in DEFAULT_CONFIG_DIRS:
            if not os.path.isdir(head): continue
            for tail in os.listdir(head):
                # only .conf files and don't override (previous paths have higer priority)
                if not tail.endswith(".conf") or tail in all_files_names: continue
                all_files_names.append(tail)
                add_config_file(head, tail)

    for d, fs in config_files.items():
        for f in fs:
            conf = read_file(os.path.join(d, f))
            for line in [l for l in conf.split("\n") if l and not (l.startswith("#") or l.isspace())]:
                fields = line.split()
                if len(fields) < 2: ewe("Wrong %s file line: %s" % (os.path.join(d, f), line))
                elif len(fields) < 7: fields.extend(["",] * (7 - len(fields)))
                elif len(fields) > 7: fields = fields[0:6] + [re.sub(".*?(%s\s+\%s.*)$" % (fields[6], fields[7]), "\\1", line)]
                for n, i in enumerate(fields):
                    if i == "-": fields[n] = ""
                create(*fields)
