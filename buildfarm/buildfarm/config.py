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
import ConfigParser

class ConfigurationFileNotFound(Exception):
    pass

class Config(object):
    """Configuration class for buildfarm configuration."""
    def __init__(self, conf_file="/etc/buildfarm/buildfarm.conf"):
        if not os.path.exists(conf_file):
            raise ConfigurationFileNotFound("Configuration file %s could not be accessed." % conf_file)

        self.__items = dict()

        self.configuration = ConfigParser.ConfigParser()
        self.configuration.read(conf_file)
        self.read()

    def read(self):
        for section in self.configuration.sections():
            self.__items.update(dict(self.configuration.items(section)))

    def __getattr__(self, attr):
        value = self.__items.get(attr, None)
        retval = value
        if value is not None:
            if value.lower() in ("true", "false"):
                # the value from ConfigParser is always string
                # check it and return bool
                retval = True if value.lower() == "true" else False
            return retval
        else:
            # value not found
            raise KeyError(attr)

# Initialize configuration object
configuration = Config()
