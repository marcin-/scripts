#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys

def main(args):

    # 1st argument is a file containing a sample queue

    sys.path.append("..")
    from dependency import DependencyResolver

    pspeclist = [l.rstrip() for l in open(sys.argv[1], "rb").readlines()]

    #print pspeclist

    # Old code
    print "Initializing old dependency resolver.."
    d1 = DependencyResolver(pspeclist, 0)

    # Patched one
    print "Initializing new dependency resolver.."
    d2 = DependencyResolver(pspeclist, 1)

    print "Resolving dependencies with the old farm code.."
    q1 = d1.resolvDeps()
    print "Resolving dependencies with the new farm code.."
    q2 = d2.resolvDeps()

    print "Old queue: %s\nNew queue: %s" % (len(q1), len(q2))
    exact = str(q1) == str(q2)
    print "Is their order the same? %s" % str(exact)

    if not exact:
        for i in range(0, len(q1)):
            print "%30s -> %30s\t[%s]" % (q1[i].rsplit('/')[-2],
                                          q2[i].rsplit('/')[-2],
                                          str(q1[i]==q2[i]))

if __name__ == "__main__":
    main(sys.argv)
