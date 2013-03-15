#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import os

from optparse import OptionParser

COMPONENT_XML = """<PISI>
    <Name>%s</Name>
</PISI>
"""
COMPONENT = """        <Component>
            <Name>%s</Name>
            <LocalName xml:lang="en">FIXME</LocalName>
            <Summary xml:lang="en">FIXME</Summary>
            <Description xml:lang="en">FIXME</Description>
            <Group>FIXME</Group>
            <Maintainer>
                <Name>PisiLinux Community</Name>
                <Email>admins@pisilinux.org</Email>
            </Maintainer>
        </Component>"""

def read_file(path):
    with open(path) as f:
        return f.read().strip()

def write_file(path, content):
    open(path, "w").write(content)
    open(path, "a").write("\n")

def check(path):
    components_xml = "%s/components.xml" % path
    name_ptrn = re.compile("\s*<Name>(.+?)<\/Name>\s*")
    mbgn_ptrn = re.compile("\s*<Maintainer>\s*")
    mend_ptrn = re.compile("\s*<\/Maintainer>\s*")
    csend_ptrn = re.compile("\s*<\/Components>\s*")
    
    cs = []
    for root, dirs, files in os.walk(path):
        c = root.split(path)[1][1:].split("/")
        if "files" in c or "comar" in c: continue
        c = ".".join(c)
        component_xml = "%s/component.xml" % root
        pspec_xml = "%s/pspec.xml" % root
        actions_py = "%s/actions.py" % root
        if not os.path.isfile(component_xml) and not os.path.isfile(pspec_xml):
            if os.path.isfile(actions_py): print "WARNING: %s not exists" % pspec_xml
            else:
                is_src_repo = False
                for r, d, f in os.walk(root):
                    if "pspec.xml" in f:
                        is_src_repo = True
                        break
                if is_src_repo and c:
                    print "%s not exists. creating..." % component_xml
                    write_file(component_xml, COMPONENT_XML % c)
        if os.path.isfile(component_xml) and c: cs.append(c) 
    
    mcs = cs[:]
    csfile = read_file(components_xml)
    maintainer = False
    new_file = []
    for line in csfile.split("\n"):
        new_file.append(line)
        if re.search(mbgn_ptrn, line): maintainer = True
        elif re.search(mend_ptrn, line): maintainer = False
        elif re.search(csend_ptrn, line):
            for m in mcs:
                new_file.insert(-1, COMPONENT % m)
        if not re.search(name_ptrn, line) or maintainer: continue
        cn = re.sub(name_ptrn, r"\1", line)
        if cn in mcs: mcs.pop(mcs.index(cn))

    new_file = "\n".join(new_file)
    write_file(components_xml, new_file)

if __name__ == "__main__":
    usage = "Usage: %prog [PATH]"
    parser = OptionParser(usage)
    parser.add_option("-c", "--check", action="store_true", dest="check", help="fix missing component.xml files and entries in components.xml")
    (options,args) = parser.parse_args()
    try:
        root = args[0]
    except IndexError:
        print "Using ./ as PATH"
        root = "./"
        
    if root.endswith("/"): root = root[:-1]
    components_xml = "%s/components.xml" % root
    if not os.path.isfile(components_xml):
        print "%s not exists!" % components_xml
        sys.exit(1)

    if options.check: check(root)