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

# PiSi module to get pspec path from package name using component name
from pisi.db.installdb import InstallDB

class QueueManager:
    def __init__(self):
        self.workQueue = []
        self.waitQueue = []

        self.workQueueFileName = "workqueue"
        self.waitQueueFileName = "waitqueue"

        self.__deserialize(self.workQueue, self.workQueueFileName)
        self.__deserialize(self.waitQueue, self.waitQueueFileName)

        # Ignore empty lines
        self.workQueue = list(set([s for s in self.workQueue if s]))
        self.waitQueue = list(set([s for s in self.waitQueue if s]))

        self.waitQueue = dependency.DependencyResolver(self.waitQueue).resolvDeps()
        self.workQueue = dependency.DependencyResolver(self.workQueue).resolvDeps()

    def __del__(self):
        self.__serialize(self.waitQueue, self.waitQueueFileName)
        self.__serialize(self.workQueue, self.workQueueFileName)

    def __serialize(self, queueName, fileName):
        try:
            queue = open(os.path.join(conf.buildfarmdir, fileName), "w")
        except IOError:
            return

        for pspec in queueName:
            queue.write("%s\n" % pspec)
        queue.close()

    def __deserialize(self, queueName, fileName):
        try:
            queue = open(os.path.join(conf.buildfarmdir, fileName), "r")
        except IOError:
            return

        for line in queue.readlines():
            if not line.startswith("#"):
                line = line.strip()
                if not os.path.exists(line):
                    # Try to guess absolute path from package name
                    try:
                        component = InstallDB().get_package(line).partOf
                    except:
                        continue

                    if component:
                        path = "%s/%s/%s/pspec.xml" % (utils.git_icin_yerel_konum(), component.replace(".", "/"), line)

                        if os.path.exists(path):
                            queueName.append(path)
                else:
                    queueName.append(line)

        queue.close()

    def set_work_queue(self, new_work_queue):
        self.workQueue = new_work_queue[:]

    def set_wait_queue(self, new_wait_queue):
        self.waitQueue = new_wait_queue[:]

    def get_work_queue(self):
        return self.workQueue

    def get_wait_queue(self):
        return self.waitQueue

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
        self.workQueue = dependency.DependencyResolver(self.workQueue).resolvDeps()
        self.waitQueue = []

    def transferToWaitQueue(self, pspec):
        self.appendToWaitQueue(pspec)
        self.removeFromWorkQueue(pspec)

class QueueManager2(QueueManager):
    def __init__(self):
        self.workQueue = []
        self.waitQueue = []

        self.workQueueFileName = "workqueue"
        self.waitQueueFileName = "waitqueue"

        self.__deserialize(self.workQueue, self.workQueueFileName)
        self.__deserialize(self.waitQueue, self.waitQueueFileName)

        # Ignore empty lines
        self.workQueue = list(set([s for s in self.workQueue if s]))
        self.waitQueue = list(set([s for s in self.waitQueue if s]))

    def __deserialize(self, queueName, fileName):
        try:
            queue = open(os.path.join(conf.buildfarmdir, fileName), "r")
        except IOError:
            return

        for line in queue.readlines():
            if not line.startswith("#"):
                line = line.strip()
                if not os.path.exists(line):
                    # Try to guess absolute path from package name
                    try:
                        component = InstallDB().get_package(line).partOf
                    except:
                        continue

                    if component:
                        path = "%s/%s/%s/pspec.xml" % (utils.git_icin_yerel_konum(), component.replace(".", "/"), line)

                        if os.path.exists(path):
                            queueName.append(path)
                else:
                    queueName.append(line)

        queue.close()

    def get_queue(self):
        return [pspec for pspec in set(self.waitQueue + self.workQueue)]
