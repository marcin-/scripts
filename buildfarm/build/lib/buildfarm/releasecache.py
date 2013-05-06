#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 TUBITAK/UEKAE
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Please read the COPYING file.

import os
import pisi
import piksemel

from buildfarm import utils
from buildfarm import logger
from buildfarm.config import configuration as conf

class ReleaseCache(object):
    """Holds a mapping of source package names to release numbers.
    This is used to fetch the release numbers of packages back in
    release time like 2011, 2011.1, etc."""

    __metaclass__ = pisi.util.Singleton

    def __init__(self):
        self.d = {}

        if not conf.basedeltarelease:
            return

        # Final local index that should exist
        local_index = os.path.join(conf.buildfarmdir, "index-%s.xml" % conf.basedeltarelease)

        if not os.path.exists(local_index):
            remote_index = utils.get_remote_tags_repository_index_url()
            try:
                index_file = pisi.file.File(remote_index,
                                            mode=pisi.file.File.read,
                                            transfer_dir=conf.buildfarmdir,
                                            compress=pisi.file.File.COMPRESSION_TYPE_AUTO)
                # Index available, rename it
                os.rename(os.path.join(conf.buildfarmdir, "pisi-index.xml"), local_index)
                os.unlink(os.path.join(conf.buildfarmdir, "pisi-index.xml.bz2"))
            except:
                logger.error("Could not fetch %s will not build delta packages against %s release!" % (remote_index,
                                                                                                       conf.basedeltarelease))
                return

        # Parse it
        doc = piksemel.parse(local_index)

        for specfile in doc.tags("SpecFile"):
            source = specfile.getTag("Source")
            name = source.getTagData("Name")

            history = specfile.getTag("History")
            update = history.getTag("Update")
            release = update.getAttribute("release")

            self.d[name] = release

    def get_last_release(self, package_name):
        """Returns the release number of package_name in the last
        release."""
        return self.d.get(package_name)
