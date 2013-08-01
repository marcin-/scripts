#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import glob

if __name__ == "__main__":
    sysdir = "/sys/bus/pci/devices/"

    for boot_vga_file in glob.glob("%s/*/boot_vga" % sysdir):
        boot_vga = open(boot_vga_file).read()[0]
        dev_path = os.path.dirname(boot_vga_file)
        vendor = open(os.path.join(dev_path, "vendor")).read().strip()
        device = open(os.path.join(dev_path, "device")).read().strip()
        print "boot_vga: %s\tvendor: %s\tdevice: %s" % (boot_vga, vendor, device)