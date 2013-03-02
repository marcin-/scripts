#!/usr/bin/python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os
import re
import sys
import fcntl
import termios

startpath = "./"
pisifiles = ("pspec.xml",
             "translations.xml")

tab = " " * 4
wsbgn = re.compile("^(\s*)")
wsend = re.compile("(\s*)$")
bgntag = re.compile(".*?<([^!\/\s>]+)[\s>].*")
endtag = re.compile(".*?<\/(\w+?)>.*")

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

if __name__ == '__main__':
    usage = "Usage: %prog [options] [PATH]"
    parser = OptionParser(usage)
    parser.add_option("-d", "--show-diff", action="store_true", dest="diff", help="show differences")
    parser.add_option("-n", "--no-write", action="store_true", dest="nowrite", help="don't write changes")
    parser.add_option("-r", "--recursive", action="store_true", dest="recursive", help="turn on recursive search for pisi xml files")
    parser.add_option("-s", "--sort", action="store_true", dest="sort", help="sort files list before fixing")
    parser.add_option("-y", "--yes-all", action="store_true", dest="yesall", help="yes to all")
    (options,args) = parser.parse_args()
    try:
        startpath = args[0]
    except IndexError:
        print "%s will be used as start path" % startpath
    if startpath.endswith("/"): startpath = startpath[:-1]

    plist = []

    if options.recursive:
        for root, dirs, files in os.walk(startpath):
            for f in pisifiles:
                if f in files: plist.append("%s/%s" % (root, f))
    else:
        for f in pisifiles:
            if f in os.walk(startpath).next()[2]: plist.append("%s/%s" % (startpath, f))

    if options.sort: plist = sorted(plist)

    for f in plist:
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
        if not i == 0: 
            print i, f
            sys.exit(1)
        new_file = "\n".join(new_file)
        print "fixing %s file" % f
        if options.diff:
            write_file("/tmp/file.orig", orig_file)
            write_file("/tmp/file.new", new_file)
            os.system("diff -usa /tmp/file.orig /tmp/file.new")
        ch = ''
        if not options.nowrite and not orig_file == new_file:
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
