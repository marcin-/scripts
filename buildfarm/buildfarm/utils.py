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
import sys
import glob
import subprocess

from buildfarm.config import configuration as conf

import pisi.util
import pisi.context as ctx

import pisi.pxml.xmlfile as xmlfile
import pisi.pxml.autoxml as autoxml
import pisi.component as component
import pisi.specfile as specfile
import pisi.metadata as metadata
import pisi.group as group
import pisi.operations
import multiprocessing

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
                    get_local_repository_url(),
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
    if conf.subrepository:
        return os.path.join(conf.repositorydir,
                            conf.release,
                            conf.subrepository)
    else:
        branch = get_git_branch()
        if branch:
            return os.path.join(conf.repositorydir,
                                branch)
        return os.path.join(conf.repositorydir,
                            conf.release)

def get_local_git_repository_url():
    repo_name = conf.scmrepositoryurl.split("/").pop()[:-4]
    branch = get_git_branch()
    if branch:
        return os.path.join(conf.repositorydir,
                            "%s-%s" % (repo_name, branch))
    if repo_name == conf.release: repo_name += "-git"  # to avoid it will the same dir as get_local_repository_url()
    return os.path.join(conf.repositorydir,
                        repo_name)

def get_remote_repository_url():
    if conf.scm == "git":
        return conf.scmrepositoryurl
    else:
        return os.path.join(conf.scmrepositorybaseurl,
                            conf.release,
                            conf.subrepository)

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
    res = []
    for path in pkg.split():
        res.append(os.path.dirname(path).partition("%s/" % get_local_repository_url())[-1])
    return " ".join(res)

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
    dist = pisi.component.Distribution("%s/distribution.xml" % get_local_repository_url())
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

def clean_waitqueue():
    open("%s/waitqueue" % conf.workdir, "w")

def clean_workqueue():
    open("%s/workqueue" % conf.workdir, "w")

class Index(xmlfile.XmlFile):
    __metaclass__ = autoxml.autoxml

    tag = "PISI"

    t_Distribution = [ component.Distribution, autoxml.optional ]
    t_Specs = [ [specfile.SpecFile], autoxml.optional, "SpecFile"]
    t_Packages = [ [metadata.Package], autoxml.optional, "Package"]
    #t_Metadatas = [ [metadata.MetaData], autoxml.optional, "MetaData"]
    t_Components = [ [component.Component], autoxml.optional, "Component"]
    t_Groups = [ [group.Group], autoxml.optional, "Group"]

    def index(self, specs):
        pool = multiprocessing.Pool()

        if specs:
            try:
                self.specs = pool.map(add_spec, specs)
            except KeyboardInterrupt:
                pool.terminate()
                pool.join()
                raise Exception

        pool.close()
        pool.join()

def add_spec(path):
    try:
        builder = pisi.operations.build.Builder(path)
        builder.fetch_component()
        sf = builder.spec
        sf.source.sourceURI = os.path.realpath(path)
        return sf

    except KeyboardInterrupt:
        raise Exception

def get_local_repo_pspecs():

    def isSpecFile(path, res = []):
        ls = os.listdir(path)
        if not ".git" in ls:
            for l in ls:
                newpath = "%s/%s" % (path, l)
                if not l == "files" and os.path.isdir(newpath):
                    isSpecFile(newpath, res)
                elif l == "pspec.xml": res.append(newpath)
        return res
        
    return sorted(isSpecFile(get_local_repository_url()))

def get_path_repo_index():
    branch = get_git_branch()
    if branch: return "%s/pisi-repo-%s-index.xml" % (conf.workdir, branch)
    return "%s/pisi-repo-index.xml" % conf.workdir

def get_path_work_index():
    branch = get_git_branch()
    if branch: return "%s/pisi-work-%s-index.xml" % (conf.workdir, branch)
    return "%s/pisi-work-index.xml" % conf.workdir

def update_local_repo_index(get_list = False):
    print "Indexing local repo ..."
    index = Index()
    index.distribution = None
    pspeclist = get_local_repo_pspecs()
    index.index(pspeclist)
    
    index.write(get_path_repo_index(), sha1sum=False, compress=None, sign=None)
    print "Index file for local repo written to %s\n" % get_path_repo_index() 
 
    if get_list: return pspeclist
 
def filter_pspec_list(pspec_list, exclude = [], verbose = True):
    binary_dir = get_compiled_packages_directory()
    missing_pkgs = set()

    for pkg in pspec_list:
        try:
            spec = pisi.specfile.SpecFile(pkg)
        except Exception, e:
            sys.stderr.write("%s\n" % e)
        else:
            if conf.architecture in spec.source.excludeArch:
                continue
            elif pkg in exclude:
                missing_pkgs.add(pkg)
                continue

            ver = spec.history[0].version
            release = spec.history[0].release

            for subpkg in spec.packages:
                expected_file = pisi.util.package_filename(subpkg.name, ver, release)
                name = subpkg.name if not subpkg.name.split("-").pop() in ["devel", "32bit", "doc", "docs", "userspace"] else subpkg.name[:-1 - len(subpkg.name.split("-").pop())]
                if os.path.exists(os.path.join(binary_dir,
                                               expected_file)) or \
                   os.path.exists(os.path.join(binary_dir,
                                               name[0:4].lower() if name.startswith("lib") and len(name) > 3 else name.lower()[0],
                                               name.lower(),
                                               expected_file)):
                    if verbose: print "Skipping: %s" % pkg
                    break
            else:
                missing_pkgs.add(pkg)    
    return sorted(list(missing_pkgs)) 

def args_checker(args, options):
    for arg in args:
        if arg.startswith("-") and len(arg) > 2:
            args[args.index(arg)] = arg[:2]
            for o in arg[2:]: args.append("-%s" % o)

    for o in options:
        if "-%s" %o in args:
            options[o] = True
            args.remove("-%s" %o)

    unknown_options = ""
    for arg in args:
        if arg.startswith("-"): unknown_options += " %s" % arg
    if unknown_options:
        sys.stderr.write("Unrecognized option%s:%s\n" % (("s" * (len(unknown_options.split()) - 1))[:1], unknown_options))
        sys.exit(1)

    return args, options

def index_workqueue(queue):
    print "Indexing work queue ..."
    index = Index()
    index.distribution = None
    index.index(queue)    
    indexfile = get_path_work_index()
    index.write(indexfile, sha1sum=False, compress=None, sign=None)
    print "Index file for work queue written to %s\n" % indexfile

def get_git_branch():
    if not os.path.isfile("%s/branch" % conf.workdir): return None
    with open("%s/branch" % conf.workdir, "r") as f:
        return f.readline().strip()

def put_git_branch(branch):
    with open("%s/branch" % conf.workdir, "w") as f:
        f.write(branch)
