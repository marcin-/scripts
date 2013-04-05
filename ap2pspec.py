#!/usr/bin/python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import glob
import sys
import os
import re

bgntag = re.compile(".*?<([^!\/\s>]+)[\s>].*")
endtag = re.compile(".*?<\/(\w+?)>.*")
level = re.compile(".*?level\s?=\s?[\'\"](\d+)[\'\"].*")
pname = re.compile(".*?>([^<]+)<.*")
workdir = re.compile("^\s*WorkDir\s*=\s*[\'\"]([^\'^\"]+)[\'\"].*?")

class Patch:
    def __init__(self, level, patch_file):
        self.level = level
        self.name = patch_file

def bgn_tag(data):
    if re.search(bgntag, data):
        return re.sub(bgntag, r"\1", data)
    return False

def end_tag(data):
    if re.search(endtag, data):
        return re.sub(endtag, r"\1", data)
    return False

def read_file(path):
    with open(path) as f:
        return f.read().strip()

def write_file(path, content):
    open(path, "w").write(content)
    open(path, "a").write("\n")

def read_spec(path):
    lines = []
    spec_file = read_file(path)
    for line in spec_file.split("\n"):
        lines.append(line)
    return lines

def get_workdir(actionfile):
    f = read_file(actionfile)
    for line in f.split("\n"):
        ret =  re.sub(workdir, r"\1", line)
        if not ret == line: return ret
    return

def get_level(line):
    ret = re.sub(level, r"\1", line)
    if ret == line: return None
    else: return ret
    
def get_pname(line):
    ret = re.sub(pname, r"\1", line)
    if ret == line: return None
    else: return ret

def cut_patches(speclines):
    new_spec = []
    found_patches = []
    patches = False
    for line in speclines:
        bt = bgn_tag(line)
        if bt == "Patches":
            patches = True
            continue
        if patches:
            et = end_tag(line)
            if et == "Patches":
                patches = False
                continue
            if bt == "Patch":
                l = get_level(line) 
                n = get_pname(line)
                if n: found_patches.append(Patch(l, n))
                continue
        new_spec.append(line)
    return new_spec, found_patches

def insert_patches(speclines, patches):
    new_spec = []
    for line in speclines:
        et = end_tag(line)
        if et == "Source":
            new_spec.append("        <Patches>")
            for p in patches:
                if p.level: new_spec.append('            <Patch level="%s">%s</Patch>' % (p.level, p.name))
                else: new_spec.append('            <Patch>%s</Patch>' % p.name)
            new_spec.append("        </Patches>")
        new_spec.append(line)
    return new_spec

def get_dest(patch):
    f = read_file(patch)
    for line in f.split("\n"):
        if line.startswith("+++"): return line.split()[1]
    print "sth wrong with def get_dest():"
    sys.exit(1)

def check_level(workdir, path):
    level = 0
    while path:
        if os.path.isfile("%s/%s" % (workdir, path)): return level
        if path.find("/") == -1: return None
        level += 1
        path = path[path.find("/")+1:]

if __name__ == '__main__':
    pisi_cmd = "pisi" if os.getenv("USER") == "root" else "sudo pisi"
    specpath = os.getcwd()

    usage = "Usage: %prog [options] [PATH]"
    parser = OptionParser(usage)
    parser.add_option("-a", "--append", dest="append", help="appends new patche(s)")
    (options,args) = parser.parse_args()
    try:
        specpath = args[0]
    except IndexError:
        pass

    if specpath.endswith("/"): specpath = specpath[:-1]
    path = specpath
    specfile = "%s/pspec.xml" % specpath
    actionfile = "%s/actions.py" % specpath

    if os.path.isfile(specfile):
        print "found %s" % specfile
    else:
        print "%s not found!" % specfile
        sys.exit(1)

    spec, patches = cut_patches(read_spec(specfile))
    workdir = get_workdir(actionfile)
    
    if options.append:
        path_glob = glob.glob(path + "/files/%s" % (options.append if not options.append.startswith("files/") else options.append[6:]))
        old_patches = []
        for p in patches:
            old_patches.append(p.name)
        os.system("%s bi %s --unpack" % (pisi_cmd, specfile))
        dirlist = filter(lambda x: os.path.isdir("/var/pisi/" + x), os.listdir("/var/pisi"))
        newest = "/var/pisi/" + max(dirlist, key=lambda x: os.stat("/var/pisi/" + x).st_mtime) + "/work"

        if workdir: workdir = os.path.normpath("%s/%s" % (newest, workdir))
        else: workdir = "%s/%s" % (newest, os.walk(newest).next()[1][0])

        for fp in path_glob:
            p = fp.split("/files/")[1]
            if not p in old_patches: 
                patches.append(Patch(check_level(workdir, get_dest(fp)), p))
        
        spec = insert_patches(spec, patches)
    
        write_file(specfile, "\n".join(spec))
