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

# E-mail message templates for mailer module..

ERROR_MESSAGE = """\
From: %(distribution)s %(release)s %(arch)s Buildfarm <%(mailFrom)s>
To: %(mailTo)s
Cc: %(ccList)s
Subject: [%(subjectID)s] %(type)s: %(subject)s
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary42"


--boundary42
Content-Type: text/plain;
            charset="utf-8"

Hello,

An error occured while building the package %(packagename)s (maintainer: %(recipientName)s).

The last 50 lines of the log before the error happens is as follows:

--------------------------------------------------------------------------
%(log)s
%(message)s
--------------------------------------------------------------------------

Plain log file: http://farm.pisilinux.org/buildlogs/%(logsdir)s/%(logfilename)s.log
Fancy log file: http://farm.pisilinux.org/buildlogs/%(logsdir)s/%(logfilename)s.html

--boundary42
Content-Type: text/html;
            charset="utf-8"

<p>Hello,<br>
An error occured while building the package <b>%(packagename)s</b> (maintainer: <b>%(recipientName)s</b>)<br>
The last 50 lines of the log before the error happens is as follows:
</p>

<div>
    <table cellpadding="5" width="100%%" style="border:1px solid #CCCCCC;">
        <tr>
            <td bgcolor="#C1CFF0">Build log for <b>%(packagename)s</b></td>
        </tr>
        <tr>
            <td bgcolor="#000000">
                <pre style="color: #FFFFFF;">%(log)s</pre>
                <pre style="color: #FF0000;">%(message)s</pre>
            </td>
        </tr>
    </table>
</div>

<p>
Plain log file:
<a href="http://farm.pisilinux.org/buildlogs/%(logsdir)s/%(logfilename)s.log">http://farm.pisilinux.org/buildlogs%(logsdir)s/%(logfilename)s.log</a><br>
Fancy log file:
<a href="http://farm.pisilinux.org/buildlogs/%(logsdir)s/%(logfilename)s.html">http://farm.pisilinux.org/buildlogs%(logsdir)s/%(logfilename)s.html</a>
</p>

<br>

--boundary42--
"""

## Info

INFO_MESSAGE = """\
From: %(distribution)s %(release)s %(arch)s Buildfarm <%(mailFrom)s>
To: %(mailTo)s
Cc: %(ccList)s
Subject: [%(subjectID)s] %(subject)s
Content-Type: text/plain;
            charset="utf-8"

Hello,

This message is sent from Pisi Linux buildfarm. Please do not reply as it is automatically generated.

%(message)s

"""

## Check info

CHECK_MESSAGE = """\
From: %(distribution)s %(release)s %(arch)s Buildfarm <%(mailFrom)s>
To: %(mailToUpdater)s
Cc: %(ccList)s
Subject: [%(subjectID)s] %(subject)s
Content-Type: text/plain;
            charset="utf-8"

Hello,

This message is sent from Pisi Linux buildfarm. Please do not reply as it is automatically generated.

%(message)s

"""

## Announce

ANNOUNCE_MESSAGE = """\
From: %(distribution)s %(release)s %(arch)s Buildfarm <%(mailFrom)s>
To: %(announceAddr)s
Subject: [%(subjectID)s] List of recently built packages
Content-Type: text/plain;
            charset="utf-8"

Hello,

This message is sent from Pisi Linux buildfarm. Please do not reply as it is automatically generated.

%(message)s

"""

# Convenience dict
ALL =  {
         'error'     : ERROR_MESSAGE,
         'announce'  : ANNOUNCE_MESSAGE,
         'info'      : INFO_MESSAGE,
         'check'      : CHECK_MESSAGE
       }
