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
#

import os

from buildfarm import dependency, utils
from buildfarm.config import configuration as conf
from buildfarm.config import CircleConfig
from buildfarm.circledepfinder import SourceDB

# PiSi module to get pspec path from package name using component name
from pisi.db.installdb import InstallDB

class QueueManager:
    def __init__(self, rdresolv = True, resolv = True):
        self.rdresolv = rdresolv

        self.workQueue = []
        self.waitQueue = []

        self.workQueueFileName = "workqueue"
        self.waitQueueFileName = "waitqueue"

        self.__deserialize(self.workQueue, self.workQueueFileName)
        self.__deserialize(self.waitQueue, self.waitQueueFileName)

        # Ignore empty lines
        self.workQueue = list(set([s for s in self.workQueue if s]))
        self.waitQueue = list(set([s for s in self.waitQueue if s]))
        
        self.circleConfig = CircleConfig()
        self.sourceDB = SourceDB(open(utils.get_path_repo_index(), "r").read())

        self.__circle_paths()
        
        if not resolv: return

        self.workQueue = dependency.DependencyResolver(self.workQueue, self.rdresolv).resolvDeps()
        self.waitQueue = dependency.DependencyResolver(self.waitQueue, self.rdresolv).resolvDeps()

    def __del__(self):
        self.__serialize(self.waitQueue, self.waitQueueFileName)
        self.__serialize(self.workQueue, self.workQueueFileName)

    def __serialize(self, queueName, fileName):
        try:
            queue = open(os.path.join(conf.buildfarmdir, fileName), "w")
        except IOError:
            return

        for line in queueName:
            for pspec in line.split():
                queue.write("%s\n" % pspec)
        queue.close()

    def __deserialize(self, queueName, fileName):
        try:
            queue = open(os.path.join(conf.buildfarmdir, fileName), "r")
        except IOError:
            return

        for line in queue.readlines():
            if not line.startswith("#"):
                for path in line.strip().split():
                    if not os.path.exists(path):
                        # Try to guess absolute path from package name
                        try:
                            component = InstallDB().get_package(path).partOf
                        except:
                            continue
    
                        if component:
                            path = "%s/%s/%s/pspec.xml" % (utils.get_local_repository_url(), component.replace(".", "/"), path)
    
                            if os.path.exists(path):
                                queueName.append(path)
                    else:
                        queueName.append(path)

        queue.close()

    def __circle_paths(self):
        '''removes circle packages paths from workQueue and append them as list of paths separated by space'''
        for circle in self.circleConfig.lines:
#            for item in circle[0]:
#                print self.sourceDB.get_source_uri(item), "OK" if self.sourceDB.get_source_uri(item) in self.workQueue else ""  
            if all(self.sourceDB.get_source_uri(item) in self.workQueue for item in circle[0]):
                paths = [self.sourceDB.get_source_uri(item) for item in circle[0]]
                for path in paths: self.workQueue.remove(path)
                self.workQueue.append(" ".join(paths))

    def set_work_queue(self, new_work_queue):
        self.workQueue = new_work_queue[:]

    def set_wait_queue(self, new_wait_queue):
        self.waitQueue = new_wait_queue[:]

    def get_work_queue(self):
        return self.workQueue

    def get_wait_queue(self):
        return self.waitQueue

    def get_queue(self):
        return [pspec for pspec in set(self.waitQueue + self.workQueue)]

    def removeFromWaitQueue(self, pspec):
        if pspec in self.waitQueue:
            self.waitQueue.remove(pspec)

    def removeFromWorkQueue(self, pspec):
        if pspec in self.workQueue:
            self.workQueue.remove(pspec)

    def dump_work_queue(self):
        if self.workQueue:
            utils.print_header("List of queued packages:")
            print "\n".join(self.workQueue)

    def dump_wait_queue(self):
        if self.waitQueue:
            utils.print_header("List of previously failed packages:")
            print "\n".join(self.waitQueue)

    def appendToWorkQueue(self, pspec):
        if pspec not in self.workQueue:
            self.workQueue.append(pspec)
            self.__serialize(self.workQueue, self.workQueueFileName)

    def appendToWaitQueue(self, pspec):
        if pspec not in self.waitQueue:
            self.waitQueue.append(pspec)
            self.__serialize(self.waitQueue, self.waitQueueFileName)

    def extend_wait_queue(self, pspecList):
        self.waitQueue = list(set(self.waitQueue + pspecList))
        self.__serialize(self.waitQueue, self.waitQueueFileName)

    def extend_work_queue(self, pspecList):
        self.workQueue = list(set(self.workQueue + pspecList))
        self.__serialize(self.workQueue, self.workQueueFileName)

    def transferToWorkQueue(self, pspec):
        self.appendToWorkQueue(pspec)
        self.removeFromWaitQueue(pspec)

    def transfer_all_packages_to_work_queue(self):
        self.workQueue = list(set(self.workQueue + self.waitQueue))
        self.workQueue = dependency.DependencyResolver(self.workQueue, self.rdresolv).resolvDeps()
        self.waitQueue = []

    def transferToWaitQueue(self, pspec):
        self.appendToWaitQueue(pspec)
        self.removeFromWorkQueue(pspec)
