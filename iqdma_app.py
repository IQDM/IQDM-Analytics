#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# iqdma_app.py
"""Start IQDM Analytics GUI"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics


import iqdma.main
import multiprocessing
from iqdma.paths import set_phantom_js_path_environment

if __name__ == "__main__":
    # Required if running from PyInstaller freeze
    # Multiprocessing library used for dose summation to avoid memory
    # allocation issues
    multiprocessing.freeze_support()

    # SVG export with Bokeh requires PhantomJS
    # Edit PATH environment so Bokeh can find phantomjs binary
    set_phantom_js_path_environment()

    iqdma.main.start()
