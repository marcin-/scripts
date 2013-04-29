# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2011 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import re
import sys
import shutil

import pisi
import pisi.context as ctx
import pisi.ui
import pisi.util

class CLI(pisi.ui.UI):
    "Command Line Interface special to buildfarm"

    def __init__(self, output, show_debug=False, show_verbose=False):
        super(CLI, self).__init__(show_debug, show_verbose)
        self.warnings = 0
        self.errors = 0
        self.output_file = output

        self.outtypes = {'Warning'  : ('brightyellow', '\033[01;33m', '#FFFF00'),
                         'Error'    : ('red', '\033[31m', '#CC0000'),
                         'Action'   : ('green', '\033[32m', '#00CC00'),
                         'Notify'   : ('cyan', '\033[36m', '#99CCFF'),
                         'Status'   : ('brightgreen', '\033[01;32m', '#00FF00'),
                         'Display'  : ('gray', '\033[0m', '#CCCCCC'),
                         'Default'  : ('default', '\033[0m', '#CCCCCC')}

        self.color_map = dict([(v, m) for k, v, m in self.outtypes.values()])

    def flush_logs(self):
        text_file = self.output_file.name
        html_file = text_file.replace(".txt", ".html")
        package = os.path.basename(text_file.split(".txt")[0])

        self.output_file.flush()
        shutil.copy(text_file, html_file)

        log_file = text_file.replace(".txt", ".log")
        _file = open(log_file, "w")
        for line in open(html_file, "r").readlines():
            line = line.rstrip('\033[0m\n') + '\n'
            match = re.match("(\033.*?m)(.*)", line)
            if match:
                _file.write("%s\n" % match.groups()[1])
            else:
                _file.write(line)

        _file.close()

        # We now have an HTML file which is an ANSI colored text file
        _file = open("%s.swp" % html_file, "w")
        _file.write("<html><head><title>Build log for %s</title></head>\n" % package)
        _file.write("<body style=\"background-color: #000000; color: #CCCCCC; font-family: Monospace\">\n")
        for line in open(html_file, "r").readlines():
            line = line.rstrip('\033[0m\n') + '\n'
            match = re.match("(\033.*?m)(.*)", line)
            if match:
                match = match.groups()
                _file.write("<span style=\"color: %s\">%s</span><br />\n" % (self.color_map.get(match[0], '\033[0m'), match[1]))
            else:
                _file.write("<span>%s</span><br />\n" % line)

        _file.write("\n</body></html>")
        _file.close()

        shutil.move("%s.swp" % html_file, html_file)

        try:
            os.unlink(text_file)
        except IOError:
            pass

    def close(self):
        pisi.util.xterm_title_reset()

    def format(self, msg, msgtype, colored=True, html=False, noln=False):
        result = ""

        # Do not use newline is noln is True
        newline = "" if noln else "\n"

        if html:
            # HTML Output
            result = "<span style=\"color: %s\">%s</span><br />\n" % (self.outtypes.get(msgtype, ['',  '', '#000000'])[2], msg)
        else:
            if not ctx.get_option('no_color'):
                if msgtype == 'Display':
                    result = msg
                elif colored and self.outtypes.has_key(msgtype):
                    result = pisi.util.colorize(msg, self.outtypes[msgtype][0]) + newline
                else:
                    result = msg + newline
            else:
                result = msgtype + ': ' + msg + newline

        return result

    def output(self, msg, msgtype=None, err=False, verbose=False, only_on_screen=False, noln=False):
        if (verbose and self.show_verbose) or (not verbose):
            if type(msg)==type(unicode()):
                msg = msg.encode('utf-8')
            if err:
                out = sys.stderr
            else:
                out = sys.stdout

            # Output to screen
            out.write(self.format(msg, msgtype, noln=noln))
            out.flush()

            if not only_on_screen:
                # Output the same stuff to the log file
                self.output_file.write(self.format(msg, msgtype, colored=True))
                self.output_file.flush()

    def info(self, msg, verbose=False, noln=False):
        self.output(unicode(msg), 'Info', verbose=verbose, noln=noln)

    def warning(self, msg):
        msg = unicode(msg)
        self.warnings += 1
        if ctx.log:
            ctx.log.warning(msg)

        self.output(msg, 'Warning', err=True, verbose=False)

    def error(self, msg):
        msg = unicode(msg)
        self.errors += 1
        if ctx.log:
            ctx.log.error(msg)

        self.output(msg, 'Error', err=True)

    def action(self, msg):
        msg = unicode(msg)
        if ctx.log:
            ctx.log.info(msg)

        self.output(msg, 'Action')

    def choose(self, msg, opts):
        msg = unicode(msg)
        prompt = msg + pisi.util.colorize(' (%s)' % "/".join(opts), 'red')
        while True:
            selection = raw_input(prompt.encode('utf-8'))
            for opt in opts:
                if opt.startswith(selection):
                    return opt

    def confirm(self, msg):
        # Modify so that it always returns True in buildfarm
        return True

    def display_progress(self, **ka):
        """ display progress of any operation """
        if ka['operation'] in ["removing", "rebuilding-db"]:
            return
        elif ka['operation'] == "fetching":
            totalsize = '%.1f %s' % pisi.util.human_readable_size(ka['total_size'])
            out = '\r%-30.50s (%s)%3d%% %9.2f %s [%s]' % \
                (ka['filename'], totalsize, ka['percent'],
                 ka['rate'], ka['symbol'], ka['eta'])
            self.output(out, 'Display', only_on_screen=True)
        else:
            self.output("\r%s (%d%%)" % (ka['info'], ka['percent']), 'Display', only_on_screen=True)

        if ka['percent'] == 100:
            self.output(' [complete]\n', 'Display')

    def status(self, msg = None):
        if msg:
            msg = unicode(msg)
            self.output(msg, 'Status')
            pisi.util.xterm_title(msg)

    def notify(self, event, **keywords):
        if event == pisi.ui.installed:
            msg = 'Installed %s' % keywords['package'].name
        elif event == pisi.ui.removed:
            msg = 'Removed %s' % keywords['package'].name
        elif event == pisi.ui.upgraded:
            msg = 'Upgraded %s' % keywords['package'].name
        elif event == pisi.ui.configured:
            msg = 'Configured %s' % keywords['package'].name
        elif event == pisi.ui.extracting:
            msg = 'Extracting the files of %s' % keywords['package'].name
        else:
            msg = None
        if msg:
            self.output(msg, 'Notify')
            if ctx.log:
                ctx.log.info(msg)
