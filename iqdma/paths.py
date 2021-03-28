#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# paths.py
"""
A collection of directories and paths updated with the script directory and
user's home folder for the OS
"""
# Copyright (c) 2016-2019 Dan Cutright
# This file is part of IQDM Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/cutright/DVH-Analytics

import sys
from os import environ, makedirs
from os.path import join, dirname, expanduser, pathsep, isdir

SCRIPT_DIR = dirname(__file__)
PARENT_DIR = getattr(
    sys, "_MEIPASS", dirname(SCRIPT_DIR)
)  # PyInstaller compatibility
RESOURCES_DIR = join(SCRIPT_DIR, "resources")
ICONS_DIR = join(RESOURCES_DIR, "icons")
WIN_FRAME_ICON = join(ICONS_DIR, "iqdma_frame.ico")
WIN_APP_ICON = join(ICONS_DIR, "iqdma.ico")
APPS_DIR = join(expanduser("~"), "Apps")
APP_DIR = join(APPS_DIR, "iqdm_analytics")
TEMP_DIR = join(APP_DIR, "temp")
OPTIONS_PATH = join(APP_DIR, ".options")
OPTIONS_CHECKSUM_PATH = join(APP_DIR, ".options_checksum")
CSV_TEMPLATES_DIR = join(APP_DIR, "csv_templates")
DEFAULT_CSV_TEMPLATES_DIR = join(RESOURCES_DIR, "csv_templates")
LICENSE_PATH = join(RESOURCES_DIR, "LICENSE.txt")
DIRECTORIES = {
    key[:-4]: value for key, value in locals().items() if key.endswith("_DIR")
}

ICONS = {
    "PDF Miner": "iconfinder_Files_Search_4903885.png",
    "Open": "iconfinder_Open_1493293.png",
    "Save": "iconfinder_Save_1493294.png",
    "Settings": "iconfinder_Settings_1493289.png",
}
for key, value in ICONS.items():
    ICONS[key] = join(ICONS_DIR, value)


def set_phantom_js_path_environment():
    """Edit the PATH environment for PhantomJS (for Bokeh's image export)"""
    phantom_js_path = getattr(sys, "_MEIPASS", APP_DIR)
    if phantom_js_path not in environ["PATH"]:
        environ["PATH"] += pathsep + phantom_js_path


def initialize_directories():
    """Create required directories if they do not exist"""
    for directory in DIRECTORIES.values():
        if not isdir(directory):
            makedirs(directory)
