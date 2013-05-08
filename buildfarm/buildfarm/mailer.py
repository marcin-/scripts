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
import smtplib

import pisi.specfile

from buildfarm.auth import Auth
from buildfarm import logger, templates, utils
from buildfarm.config import configuration as conf


def send(msg, pspec = "", _type = "", subject=""):

    if not conf.sendemail:
        logger.info("Sending of notification e-mails is turned off.")
        return


    # Authentication stuff
    (username, password) = Auth().get_credentials("Mailer")

    # subjectID: ex: [release/{devel,stable}/arch]
    subject_id = "%s/%s/%s" % (conf.release.capitalize(),
                               conf.subrepository,
                               conf.architecture)

    logs_dir = "%s/%s/%s" % (conf.release,
                             conf.subrepository,
                             conf.architecture)


    recipients_name, recipients_email = [], []
    logfilename = ""
    package_name_with_component = ""
    package_name = ""
    last_log = []
    if pspec:
        spec = pisi.specfile.SpecFile(os.path.join(utils.get_local_repository_url(), pspec))
        recipients_name.append(spec.source.packager.name)
        recipients_email.append(spec.source.packager.email)

        package_name = os.path.basename(os.path.dirname(pspec))
        package_name_with_component = utils.get_package_component_path(pspec)

        logfile = os.path.join(utils.get_package_log_directory(),
                               utils.get_package_logfile_name(pspec))
        logfilename = os.path.splitext(os.path.basename(logfile))[0]

        last_log = open(logfile.replace(".txt", ".log")).read().split("\n")[-50:]

    message = templates.ALL[_type] % {
                                        'log'          : "\n".join(last_log),
                                        'recipientName': " ".join(recipients_name),
                                        'mailTo'       : ", ".join(recipients_email),
                                        'ccList'       : conf.cclist,
                                        'mailFrom'     : conf.mailfrom,
                                        'announceAddr' : conf.announceaddr,
                                        'subject'      : package_name_with_component or subject or _type,
                                        'message'      : msg,
                                        'pspec'        : pspec,
                                        'type'         : _type,
                                        'packagename'  : package_name,
                                        'logfilename'  : logfilename,
                                        'distribution' : conf.name,
                                        'release'      : conf.release.capitalize(),
                                        'arch'         : conf.architecture,
                                        'logsdir'      : logs_dir,
                                        'subjectID'    : subject_id,
                                     }

    try:
        session = smtplib.SMTP(conf.smtpserver, timeout=10)
    except smtplib.SMTPConnectError:
        logger.error("Failed sending e-mail: Couldn't open session on %s." % conf.smtpserver)
        return

    try:
        session.login(username, password)
    except smtplib.SMTPAuthenticationError:
        logger.error("Failed sending e-mail: Authentication failed.")
        return

    try:
        if _type == "announce":
            session.sendmail(conf.mailfrom, conf.announceaddr, message)
        else:
            session.sendmail(conf.mailfrom, recipients_email + conf.cclist.split(","), message)
    except smtplib.SMTPException:
        logger.error("Failed sending e-mail: sendmail() raised an exception.")

def error(message, pspec, subject=""):
    send(message, pspec, _type="error", subject=subject)

def info(message, subject=""):
    send(message, _type="info", subject=subject)

def announce(message, subject=""):
    send(message, _type="announce", subject=subject)
