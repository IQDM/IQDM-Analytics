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
from iqdma.paths import set_phantom_js_path_environment

if __name__ == "__main__":

    set_phantom_js_path_environment()

    iqdma.main.start()
