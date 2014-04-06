#!/usr/bin/python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os
import re
import sys
import fcntl
import termios

startpath = "./"
pisifilesxml = ("pspec.xml",
             "translations.xml")

tab = " " * 4
wsbgn = re.compile("^(\s*)")
wsend = re.compile("(\s*)$")
bgntag = re.compile(".*?<([^!\/\s>]+)[\s>].*")
endtag = re.compile(".*?<\/(\w+?)>.*")
bgndep = re.compile("<(Runtime|Build)Dependencies>")
enddep = re.compile("<\/(Runtime|Build)Dependencies>")
depvr = re.compile(".*Dependency([^<]+)<\/.*")
dep = re.compile(".*>([^<]+)<\/.*")
bgncfg = re.compile("^(\s+\w+\.(raw)?[cC]onfigure\([\'\"])(.*)")
endcfg = re.compile("\s+(\S*)\s*?([\'\"\)]?.*\)\s*)$")
pline = re.compile("(\s*)(.+?)(\s*\\\s*)$")

def remove_wsbgn(data):
    return re.sub(wsbgn, "", data)

def remove_wsend(data):
    return re.sub(wsend, "", data)

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

def getch():
    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    try:
        while 1:
            try:
                ch = sys.stdin.read(1)
                break
            except IOError: pass
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    return ch

def len_sorted(a, vr=True):
    d = {}
    for i in a: d[i] = len(re.sub(depvr if vr else dep, "\\1", i))
    return [i[0] for i in sorted(d.items(), key=lambda x:x[1])]

def write_new_file(new_file, old_file):
    ch = ''
    if not options.nowrite and not old_file == new_file:
        if not options.yesall:
            print "Write changes? [Y/n]"
            while not (ch == 'y' or ch == 'n' or ch == '\n'):
                ch = getch()
            if ch == "\n": ch = 'y'
            print ch
        if ch == 'y'or options.yesall: write_file(f, new_file)
    elif not options.yesall:
        print "press a key"
        ch = getch()

if __name__ == '__main__':
    usage = "Usage: %prog [options] [PATH]"
    parser = OptionParser(usage)
    parser.add_option("-d", "--show-diff", action="store_true", dest="diff", help="show differences")
    parser.add_option("-n", "--no-write", action="store_true", dest="nowrite", help="don't write changes")
    parser.add_option("-r", "--recursive", action="store_true", dest="recursive", help="turn on recursive search for pisi xml files")
    parser.add_option("-a", "--clean-actions", action="store_true", dest="actions", help="clean actions.py")
    parser.add_option("-s", "--sort", action="store_true", dest="sort", help="sort build and runtime dependencies")
    parser.add_option("-l", "--sortlen", action="store_true", dest="sortlen", help="sort by lenght build and runtime dependencies")
    parser.add_option("-L", "--sortlenvr", action="store_true", dest="sortlenvr", help="sort by lenght build and runtime dependencies (with dependency arg)")
    parser.add_option("-y", "--yes-all", action="store_true", dest="yesall", help="yes to all")
    (options,args) = parser.parse_args()
    try:
        startpath = args[0]
    except IndexError:
        print "%s will be used as start path" % startpath
    if startpath.endswith("/"): startpath = startpath[:-1]

    pxlist = []
    palist = []

    if options.recursive:
        for root, dirs, files in os.walk(startpath):
            for f in pisifilesxml:
                if f in files: pxlist.append("%s/%s" % (root, f))
                elif f == "actions.py": palist.append("%s/%s" % (root, f))
    else:
        if os.path.isfile("%s/actions.py" % startpath): palist.append("%s/actions.py" % startpath)
        for f in pisifilesxml:
            if f in os.walk(startpath).next()[2]: pxlist.append("%s/%s" % (startpath, f))

    pxlist = sorted(pxlist)
    palist = sorted(palist)

    if options.actions:
        for f in palist:
            orig_file = read_file(f)
            new_file = []
            params = []
            append_param = False
            firstline = ""
            lastline = "" 
            for line in orig_file.split("\n"):
                if line.isspace(): line = ""
                if re.search(bgncfg, line) and not re.search(endcfg, line):
                    firstline = re.sub(bgncfg, "\\1", line)
                    params.append(re.sub(pline, "\\2", re.sub(bgncfg, "\\3", line)))
                    append_param = True
                elif append_param:
                    if re.search(endcfg, line):
                        append_param = False
                        if re.sub(endcfg, "\\1", line): params.append(re.sub(endcfg, "\\1", line))
                        lastline = re.sub(endcfg, "\\2", line)
                    else:
                        params.append(re.sub(pline, "\\2", line))
                    if not append_param:
                        if params[-1][-1].endswith(firstline[-1]):
                            lastline = params[-1][-1] + lastline 
                            params[-1] = params[-1][:-1]
                        new_file.append(firstline + "\\")
                        for p in sorted([" " + i if "/" in i else i for i in params]):
                            if not p or p.isspace(): continue
                            new_file.append("%s%s \\" % (" " * (len(firstline) + (1 if not p.startswith(" ") else 0)), p))
                        new_file.append(" " * (len(firstline) - 1) + lastline)
                else: new_file.append(line)
            write_new_file("\n".join(new_file), orig_file)
            print "fixing %s file" % f
            if options.diff:
                write_file("/tmp/file.orig", orig_file)
                write_file("/tmp/file.new", new_file)
                os.system("diff -usa /tmp/file.orig /tmp/file.new")

    for f in pxlist:
        orig_file = read_file(f)
        new_file = []
        i = 0
        for line in orig_file.split("\n"):
            if line.isspace(): line = ""
            if line.startswith("<?") or line.startswith("<!"):
                new_file.append(line)
                continue
            elif remove_wsbgn(line).startswith("<"):
                bt = bgn_tag(line)
                et = end_tag(line)
                if et and not bt: i = i - 1
                line = re.sub(wsend, "", line)
                new_file.append(re.sub(wsbgn, tab * i, line))
                if bt and not et: i = i + 1
                if i < 0: sys.exit(1)
            else: 
                if end_tag(line): i = i - 1
                new_file.append(line)
        
        sorted_file = []
        if not i == 0: 
            print i, f
            sys.exit(1)
        elif options.sort or options.sortlen or options.sortlenvr:
            append_deps = False
            deps = []
            for l in new_file:
                if re.search(bgndep, l): append_deps = True
                elif re.search(enddep, l):
                    sorted_file.append(deps[0])
                    if options.sortlen: sorted_file.extend(len_sorted(deps[1:], vr=False))
                    elif options.sortlenvr: sorted_file.extend(len_sorted(deps[1:], vr=True))
                    else: sorted_file.extend(sorted(deps[1:]))
                    append_deps = False
                    deps = []
                if append_deps: deps.append(l)
                else: sorted_file.append(l)
        new_file = "\n".join(sorted_file if sorted_file else new_file)
        print "fixing %s file" % f
        if options.diff:
            write_file("/tmp/file.orig", orig_file)
            write_file("/tmp/file.new", new_file)
            os.system("diff -usa /tmp/file.orig /tmp/file.new")
        write_new_file(new_file, orig_file)
