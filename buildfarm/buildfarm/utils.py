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

# Various helper functions for pisi packages

import os
import glob
import subprocess

from buildfarm.config import configuration as conf

import pisi.util
import pisi.context as ctx

def print_header(msg):
    print "\n%s\n%s\n" % (msg, '-'*len(msg))

def is_there_free_space(directory=None):
    """Returns the free space in the device."""
    if os.path.isdir("/var/pisi") == False:
        os.system("mkdir /var/pisi")
        print "/var/pisi dizini oluşturuluyor."
    if not directory:
        # Defaults to /var/pisi
        directory = ctx.config.values.dirs.tmp_dir
    _stat = os.statvfs(directory)
    free_space = _stat.f_bfree * _stat.f_bsize

    print "Free space: %s GB" % (free_space/(1024*1024*1024.0))

    # Return True if the free space >= 5GB
    return free_space >= (5*1024*1024*1024)

def mount_tmpfs(size="10G"):
    """Mounts pisi tmp_dir within a tmpfs of 10G size."""
    subprocess.call(["/bin/mount",
                     "tmpfs", "-t", "tmpfs",
                     ctx.config.values.dirs.tmp_dir,
                     "-o", "size=%s,noatime" % size])

def umount_tmpfs():
    """Unmount tmp_dir if mounted."""
    if conf.usetmpfs and \
        ctx.config.values.dirs.tmp_dir in \
        open("/proc/self/mountinfo").readlines():
        subprocess.call(["/bin/umount",
                         ctx.config.values.dirs.tmp_dir])

def create_directories():
    directories = [
                    conf.workdir,
                    conf.buildfarmdir,
                    conf.repositorydir,
                    conf.logdir,
                    get_compiled_packages_directory(),
                    get_compiled_debug_packages_directory(),
                    git_icin_yerel_konum(),
                    get_package_log_directory(),
                  ]

    for directory in directories:
        if directory and not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError:
                print "Directory %s cannot be created." % directory

def get_distribution_release():
    return conf.release

def get_local_repository_url():
    return os.path.join(conf.repositorydir,
                        conf.release,
                        conf.subrepository)

def git_icin_yerel_konum():
    return conf.repositorydir

def get_remote_repository_url():
    return os.path.join(conf.scmrepositorybaseurl,
                        conf.release,
                        conf.subrepository)

def git_icin_uzak_konum():
    return conf.scmrepositorybaseurl


def get_remote_tags_repository_index_url():
    if conf.basedeltarelease:
        return os.path.join(conf.scmrepositorybaseurl,
                            "tags",
                            conf.basedeltarelease,
                            "pisi-index.xml.bz2")

def get_package_log_directory():
    return os.path.join(conf.logdir,
                        conf.release,
                        conf.subrepository,
                        conf.architecture)

def get_compiled_packages_directory():
    return os.path.join(conf.binarypath,
                        conf.release,
                        conf.subrepository,
                        conf.architecture)

def get_compiled_debug_packages_directory():
    return "%s-debug" % get_compiled_packages_directory()

def get_stable_packages_directory():
    """Return the stable packages repository if this is a testing buildfarm."""
    if conf.subrepository == "testing":
        # Must have a corresponding stable repository
        return os.path.join(conf.binarypath,
                            conf.release,
                            "stable",
                            conf.architecture)
    else:
        return None

def get_stable_debug_packages_directory():
    """Return the stable debug packages repository if this is a testing buildfarm."""
    stable_packages_directory = get_stable_packages_directory()
    if stable_packages_directory:
        return "%s-debug" % stable_packages_directory
    else:
        return None

def get_expected_file_name(spec):
    last_update = spec.history[0]

    # e.g. kernel-2.6.32.24-143-p11-x86_64.pisi if the last update's
    # version is 2.6.32.24 and the release is 143.
    return pisi.util.package_filename(spec.packages[0].name,
                                      last_update.version,
                                      last_update.release)

def get_package_logfile_name(pkg):
    spec = pisi.specfile.SpecFile(pkg)
    last_update = spec.history[0]
    return "%s-%s-%s.txt" % (get_package_name_from_path(pkg),
                             last_update.version,
                             last_update.release)

def get_package_name(pkg):
    return pisi.util.split_package_filename(pkg)[0]

def get_package_name_from_path(pkg):
    return os.path.basename(os.path.dirname(pkg))

def get_package_component_path(pkg):
    """Extracts system/base/gettext from full path."""
    return os.path.dirname(pkg).partition("%s/" % \
            git_icin_yerel_konum())[-1]

def delete_pisi_files_from(directory):
    """Deletes all .pisi files found in directory."""
    for pisi_file in glob.glob("%s/*%s" % (directory.rstrip("/"),
                                           ctx.const.package_suffix)):
        try:
            os.unlink(pisi_file)
        except OSError:
            pass

def run_hooks():
    """Runs hooks found in conf.hookdir."""
    hooks = sorted(glob.glob("%s/[0-9][0-9]-*" % conf.hookdir))

    for hook in hooks:
        if os.access(hook, os.X_OK):
            # Execute it asynchronously
            subprocess.Popen(hook,
                             stdout=open("/dev/null", "w"),
                             stderr=subprocess.STDOUT).pid

def remove_obsoleted_packages():
    """Removes obsoleted packages from the system."""
    # Use directly distributions.xml to not rely on available
    # repositories on the system.
    dist = pisi.component.Distribution("%sdistribution.xml" % git_icin_yerel_konum())
    obsoletes = [obsolete.package for obsolete in dist.obsoletes]

    # Reduce the list so that already removed ones are excluded
    obsoletes = list(set(obsoletes).intersection(pisi.api.list_installed()))

    if obsoletes:
        pisi.api.remove(obsoletes)

    return obsoletes

def is_arch_excluded(spec):
    """Returns True if the given pspec.xml shouldn't be built
    on the current architecture."""
    return ctx.config.values.get("general", "architecture") \
            in spec.source.excludeArch

def is_delta_package(pkg):
    return pkg.endswith(ctx.const.delta_package_suffix)

def is_debug_package(pkg):
    package_name = get_package_name(pkg)
    return package_name.endswith(ctx.const.debug_name_suffix)
