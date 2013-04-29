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

import pisi.api
import pisi.config

from buildfarm import cli, logger, utils
from buildfarm.releasecache import ReleaseCache
from buildfarm.config import configuration as conf


class PisiApi:
    def __init__(self, stdout=None, stderr=None, output_dir = conf.workdir):
        self.options = pisi.config.Options()

        # Override these so that pisi searches for .pisi files in the right locations
        self.options.output_dir = output_dir

        self.options.yes_all = True
        self.options.ignore_file_conflicts = True
        self.options.ignore_package_conflicts = True
        self.options.debug = True
        self.options.verbose = True
        self.options.ignore_check = conf.ignorecheck
        self.options.ignore_sandbox = False

        # Set API options
        pisi.api.set_options(self.options)

        # Set IO streams
        pisi.api.set_io_streams(stdout=stdout, stderr=stderr)

        pisi.api.set_userinterface(cli.CLI(stdout))

        self.builder = None

    def get_new_packages(self):
        return self.builder.new_packages

    def get_new_debug_packages(self):
        return self.builder.new_debug_packages

    def get_delta_package_map(self):
        # Return type is a dictionary
        return self.builder.delta_map

    def close(self):
        pisi.api.ctx.ui.flush_logs()

    def build(self, pspec):
        if not os.path.exists(pspec):
            logger.error("'%s' does not exist." % pspec)

        if conf.sandboxblacklist and \
                utils.get_package_name_from_path(pspec) in conf.sandboxblacklist:
            logger.info("Disabling sandbox for %s" % pspec)
            pisi.api.ctx.set_option("ignore_sandbox", True)

        logger.info("Building %s" % pspec)
        self.builder = pisi.operations.build.Builder(pspec)

        # This will only make builder search for old packages
        # 2 packages for testing repository
        self.builder.search_old_packages_for_delta(max_count=2,
                                                   search_paths=(utils.get_compiled_packages_directory(),))
        if utils.get_stable_packages_directory():
            # 3 packages for stable repository
            self.builder.search_old_packages_for_delta(max_count=3,
                                                       search_paths=(utils.get_stable_packages_directory(),))

            # and 1 for the previous distribution release (e.g. 2011.1)
            package_name = utils.get_package_name_from_path(pspec)
            last_distro_release = ReleaseCache().get_last_release(package_name)
            if last_distro_release:
                self.builder.search_old_packages_for_delta(release=last_distro_release,
                                                           search_paths=(utils.get_stable_packages_directory(),))

        self.builder.build()

        logger.info("Created package(s): %s" % self.builder.new_packages)

    def install(self, pkgs):
        pisi.api.install(pkgs, ignore_file_conflicts=self.options.ignore_file_conflicts,
                               ignore_package_conflicts=self.options.ignore_package_conflicts,
                               reinstall=True)

