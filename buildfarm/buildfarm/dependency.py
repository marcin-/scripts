#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2011 TUBITAK/UEKAE
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Please read the COPYING file.

import os
import sys

import pisi.specfile

from buildfarm import utils
from buildfarm import logger
from buildfarm.config import configuration as conf

class DependencyResolver:
    def __init__(self, pspeclist, rdresolv = True):

        self.resolvrdeps = rdresolv

        self.oldwd = os.getcwd()
        os.chdir(utils.get_local_repository_url())

        # Work queue and wait queue may contain same pspecs.
        # be sure that every pspec is unique in the pspeclist.
        self.pspeclist = [pspec for pspec in set(pspeclist)]

        self.bdepmap, self.rdepmap, self.namemap, self.srcnamemap, self.pspeccount = {}, {}, {}, {}, len(self.pspeclist)

        for pspec in self.pspeclist:
            if len(pspec.split()) == 1: self.bdepmap[pspec] = self.__getBuildDependencies(pspec)
            else:
                for path in pspec.split():
                    try:
                        self.bdepmap[pspec] += self.__getBuildDependencies(path)
                    except KeyError:
                        self.bdepmap[pspec] = self.__getBuildDependencies(path)
                self.bdepmap[pspec] = list(set(self.bdepmap[pspec]))
                for path in pspec.split():
                    for pkg in self.__getPackageNames(path):
                        if pkg in self.bdepmap[pspec]: self.bdepmap[pspec].remove(pkg)
        for pspec in self.pspeclist:
            if len(pspec.split()) == 1: self.rdepmap[pspec] = self.__getRuntimeDependencies(pspec)
            else:
                for path in pspec.split():
                    try:
                        self.rdepmap[pspec] += self.__getRuntimeDependencies(path)
                    except KeyError:
                        self.rdepmap[pspec] = self.__getRuntimeDependencies(path)
        for pspec in self.pspeclist:
            if len(pspec.split()) == 1:
                self.namemap[pspec] = self.__getPackageNames(pspec)
                self.srcnamemap[pspec] = self.__getSrcName(pspec)                
            else:
                for path in pspec.split():
                    try:
                        self.namemap[pspec] += self.__getPackageNames(path)
                        self.srcnamemap[pspec] += self.__getSrcName(path)                
                    except KeyError:
                        self.namemap[pspec] = self.__getPackageNames(path)
                        self.srcnamemap[pspec] = self.__getSrcName(path)

    def get_srcName(self, src):
        return self.srcnamemap[src]

    def get_buildDeps(self, src):
        return self.bdepmap[src]

    def resolvDeps(self):
        if self.resolvrdeps:
            while not (self.buildDepResolver() and self.runtimeDepResolver()):
                pass
        else:
            while not self.buildDepResolver():
                pass

        #os.chdir(self.oldwd)
        return self.pspeclist

    def __getBuildDependencies(self, pspec):
        specFile = pisi.specfile.SpecFile()
        try:
            specFile.read(pspec)
        except:
            logger.error("Could not read pspec file: %s" % pspec)
            sys.exit(1)

        deps = []
        for package in specFile.source.buildDependencies:
            deps += [package.package]

        return deps

    def __getRuntimeDependencies(self, pspec):
        try:
            specFile = pisi.specfile.SpecFile(pspec)
        except:
            logger.error("Could not read pspec file: %s" % pspec)
            sys.exit(1)

        deps = []
        for package in specFile.packages:
            for dep in package.runtimeDependencies():
                deps += [dep.package]

        deps = list(set(deps).difference(set([p.name for p in specFile.packages])))

        return deps

    def __getPackageNames(self, pspec):
        try:
            specFile = pisi.specfile.SpecFile(pspec)
        except:
            logger.error("Could not read pspec file: %s" % pspec)
            sys.exit(1)

        try:
            return [package.name for package in specFile.packages]
        except:
            return [""]

    def __getSrcName(self, pspec):
        try:
            specFile = pisi.specfile.SpecFile(pspec)
        except:
            logger.error("Could not read pspec file: %s" % pspec)
            sys.exit(1)

        try:
            return specFile.source.name
        except:
            return None

    def runtimeDepResolver(self):
        """Arranges the order of the pspec's in the pspeclist to satisfy runtime deps"""
        clean = True
        for i in range(0, self.pspeccount):
            pspec = self.pspeclist[i]
            for p in self.rdepmap.get(pspec):
                for j in range(i+1, self.pspeccount):
                    if p in self.namemap.get(self.pspeclist[j]):
                        self.pspeclist.insert(j+1, self.pspeclist.pop(i))
                        clean = False
        #if not clean: print "runtime deps not resolved"
        return clean


    def buildDepResolver(self):
        """Arranges the order of the pspec's in the pspeclist to satisfy build deps"""
        clean = True
        for i in range(0, self.pspeccount):
            pspec = self.pspeclist[i]
            # Current pspec: pspec
            for p in self.bdepmap.get(pspec):
                # Traverse build dependency list of 'pspec' with p
                for j in range(i+1, self.pspeccount):
                    # For each pspec in queue, check if p exists
                    # in its packages
                    if p in self.namemap.get(self.pspeclist[j]):
                        # namemap brings package list of a package
                        #print self.pspeclist[i].split('/')[-2], self.pspeclist[j].split('/')[-2]
                        self.pspeclist.insert(j+1, self.pspeclist.pop(i))
                        clean = False
                        #print "build deps not resolved"
        return clean
