#!/usr/bin/python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import glob
import sys
import os
import re

bgntag = re.compile("^\s*?<([^!\/\s>]+)[\s>].*")
endtag = re.compile(".*?<\/(\w+?)>\s*$")
bgnnote = re.compile("^\s*<!--\s*")
endnote = re.compile("\s*-->\s*$")
bgndisabledpatch = re.compile("^\s*<!--\s*<?\s*Patch(>|\s*level)")
enddisabledpatch = re.compile("<\/Patch>?\s*-->\s*$")
level = re.compile(".*?level\s?=\s?[\'\"](\d+)[\'\"].*")
pname = re.compile(".*?>([^<]+)<.*")
workdir = re.compile("^\s*WorkDir\s*=\s*[\'\"]([^\'^\"]+)[\'\"].*?")

class Patch:
    def __init__(self, level, patch_file, enabled=True):
        self.level = level
        self.name = patch_file
        self.enabled = enabled

class PatchNote:
    def __init__(self, index, note):
        self.index = index
        self.note = note

def get_notes_dict(notes):
    notes_dict = {}
    for n in notes:
        try:
            notes_dict[n.index].append(n.note)
        except KeyError:
            notes_dict[n.index] = [n.note]
    return notes_dict

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
    found_notes = []
    found_patches = []
    patches = False
    disabled_patches = False
    comment = False
    for line in speclines:
        bt = bgn_tag(line)
        if bt == "Patches":
            patches = True
            continue
        if patches:
            enabled = True
            if re.search(bgndisabledpatch, line):
                disabled_patches = True
                line = re.sub(bgndisabledpatch, r"<Patch\1", line)
                bt = bgn_tag(line)
            elif re.search(bgnnote, line):
                comment = True
                line = re.sub(bgnnote, "", line)
            if disabled_patches: enabled = False
            if comment:
                if re.search(endnote, line):
                    comment = False
                    line = re.sub(endnote, "", line)
                line = re.sub("^\s*", "", line)
                found_notes.append(PatchNote(len(found_patches), line))
                continue
            if re.search(enddisabledpatch, line):
                disabled_patches = False
                line = re.sub(enddisabledpatch, "</Patch>", line)
            et = end_tag(line)
            if et == "Patches":
                patches = False
                continue
            if bt == "Patch":
                l = get_level(line) 
                n = get_pname(line)
                if n: found_patches.append(Patch(l, n, enabled))
                continue
            if not line or line.isspace(): continue
        new_spec.append(line)
    return new_spec, found_patches, found_notes

def insert_patches(speclines, patches, notes):
    dict_notes = get_notes_dict(notes)
    new_spec = []
    for line in speclines:
        et = end_tag(line)
        if et == "Source":
            new_spec.append("        <Patches>")
            cp = 0
            for p in patches:
                if cp in dict_notes:
                    cn = 0
                    ln = len(dict_notes[cp])
                    nline = ""
                    for n in dict_notes[cp]:
                        if cn == 0: nline = "            <!-- "
                        else: nline = "     "
                        nline = nline + n
                        if cn + 1 == ln: nline = nline + " -->" 
                        new_spec.append(nline)
                if p.level:
                    if p.enabled: new_spec.append('            <Patch level="%s">%s</Patch>' % (p.level, p.name))
                    else: new_spec.append('            <!--Patch level="%s">%s</Patch-->' % (p.level, p.name))
                else:
                    if p.enabled: new_spec.append('            <Patch>%s</Patch>' % p.name)
                    else: new_spec.append('            <!--Patch>%s</Patch-->' % p.name)
                cp += 1
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

def get_all_patch_files(path):
    path = path.split("/files")[0]
    path = "%s/files" % path
    patch_files_in_root = []
    patch_files_in_subdirs = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith("patch") or f.endswith("diff"):
                if root == path: patch_files_in_root.append(f)
                else: patch_files_in_subdirs.append("%s/%s" % (root.replace(path, "")[1:], f))
    return sorted(patch_files_in_root) + sorted(patch_files_in_subdirs)

if __name__ == '__main__':
    pisi_cmd = "pisi" if os.getenv("USER") == "root" else "sudo pisi"
    specpath = os.getcwd()

    usage = "Usage: %prog [options] [PATH]"
    parser = OptionParser(usage)
    parser.add_option("-a", "--append", dest="append", help="appends new patche(s)")
    parser.add_option("-l", "--list-patches", action="store_true", dest="list", help="list pspec patches")
    parser.add_option("-n", "--list-new-patches", action="store_true", dest="listnew", help="list new patches")
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

    spec, patches, patch_notes = cut_patches(read_spec(specfile))
    workdir = get_workdir(actionfile)
          
    def get_old_patches(patches):
        old_patches = []
        for p in patches:
            old_patches.append(p.name)
        return old_patches

    def get_new_patches(patches, path):
        new_patches = []
        old_patches = get_old_patches(patches)
        for p in get_all_patch_files(path):
            if not p in old_patches:
                new_patches.append(p)
        return new_patches

    if options.append:
        os.system("%s bi %s --unpack" % (pisi_cmd, specfile))
        dirlist = filter(lambda x: os.path.isdir("/var/pisi/" + x), os.listdir("/var/pisi"))
        newest = "/var/pisi/" + max(dirlist, key=lambda x: os.stat("/var/pisi/" + x).st_mtime) + "/work"

        if workdir: workdir = os.path.normpath("%s/%s" % (newest, workdir))
        else: workdir = "%s/%s" % (newest, os.walk(newest).next()[1][0])

        path_glob = glob.glob(path + "/files/%s" % (options.append if not options.append.startswith("files/") else options.append[6:]))
        old_patches = get_old_patches(patches)
        for fp in path_glob:
            p = fp.split("/files/")[1]
            if not p in old_patches: 
                patches.append(Patch(check_level(workdir, get_dest(fp)), p))
        
        spec = insert_patches(spec, patches, patch_notes)
    
        write_file(specfile, "\n".join(spec))

    if options.list:
        print "--- current patches (used in pspec.xml) ---"
        c = 0
        notes_dict = get_notes_dict(patch_notes)
        for p in patches:
            if c in notes_dict:
                for n in notes_dict[c]:
                    print "# %s" % n
            c += 1
            print ("%d\t%s %s %s" % (c, ("E" if p.enabled else "D"), (p.level if p.level else "0"), p.name))
        if c in notes_dict:
            for n in notes_dict[c]:
                print "# %s" % n

    if options.listnew:
        print "--- new patches (not used in pspec.xml) ---"
        c = 0
        for p in get_new_patches(patches, path):
            c += 1
            print "%d\t%s" % (c, p)
