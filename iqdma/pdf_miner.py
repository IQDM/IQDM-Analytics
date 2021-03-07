#!/usr/bin/env python
# -*- coding: utf-8 -*-

# threading_progress.py
"""
Generic classes to perform threading with a progress frame
"""
# Copyright (c) 2020 Dan Cutright
# This file is part of DVHA DICOM Editor, released under a BSD license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/cutright/DVHA-DICOM-Editor

import wx
from IQDMPDF.file_processor import process_files
from threading import Thread
from pubsub import pub


class ProgressFrame(wx.Dialog):
    """Create a window to display progress and begin provided worker"""

    def __init__(self, iqdm_pdf_kwargs):
        wx.Dialog.__init__(self, None)

        self.iqdm_pdf_kwargs = iqdm_pdf_kwargs

        self.gauge = wx.Gauge(self, wx.ID_ANY, 100)
        self.label_progress = wx.StaticText(self, wx.ID_ANY, "Initializing...")
        self.label_elapsed = wx.StaticText(self, wx.ID_ANY, "")
        self.label_remaining = wx.StaticText(self, wx.ID_ANY, "")

        self.__set_properties()
        self.__do_layout()

        pub.subscribe(self.update, "progress_update")

        self.run()

    def run(self):
        """Initiate layout in GUI and begin thread"""
        self.Show()
        ProgressFrameWorker(self.iqdm_pdf_kwargs)

    def callback(self, msg):
        wx.CallAfter(self.gauge.SetValue, int(msg.split('%|')[0]))

    def __set_properties(self):
        self.SetMinSize((672, 100))
        self.SetTitle('Running IQDM-PDF')

    def __do_layout(self):
        sizer_wrapper = wx.BoxSizer(wx.VERTICAL)
        sizer_time = wx.BoxSizer(wx.HORIZONTAL)
        sizer_wrapper.Add(self.label_progress, 0, wx.TOP | wx.LEFT, 10)
        sizer_wrapper.Add(self.gauge, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer_time.Add(self.label_elapsed, 1, wx.EXPAND | wx.LEFT, 10)
        sizer_time.Add(self.label_remaining, 0, wx.RIGHT, 10)
        sizer_wrapper.Add(sizer_time, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_wrapper)
        self.Fit()
        self.Layout()
        self.Center()

    def set_title(self, msg):
        wx.CallAfter(self.SetTitle, msg)

    def update(self, msg):
        progress = f"Processing File: {msg['progress']}"
        elapsed = f"Elapsed: {msg['elapsed']}"
        remaining = f"Est. Remaining: {msg['remaining']}"
        wx.CallAfter(self.label_progress.SetLabelText, progress)
        wx.CallAfter(self.label_elapsed.SetLabelText, elapsed)
        wx.CallAfter(self.label_remaining.SetLabelText, remaining)
        wx.CallAfter(self.gauge.SetValue, int(100 * msg["gauge"]))
        wx.CallAfter(self.Layout)
        if msg["gauge"] == 1:
            self.close()

    def close(self):
        pub.unsubAll(topicName="progress_update")
        wx.CallAfter(self.Destroy)


class ProgressFrameWorker(Thread):
    """Create a thread, perform action on each item in obj_list"""

    def __init__(self, iqdm_pdf_kwargs):
        Thread.__init__(self)
        self.iqdm_pdf_kwargs = iqdm_pdf_kwargs
        self.iqdm_pdf_kwargs['callback'] = self.callback
        self.start()

    def run(self):
        process_files(**self.iqdm_pdf_kwargs)

    @staticmethod
    def callback(msg):
        gauge = 100 if msg == 'complete' else int(msg.split('%|')[0])
        if msg == 'complete':
            progress = elapsed = remaining = ''
        else:
            progress = msg.split('| ')[1].split(' ')[0]
            elapsed = msg.split('[')[1].split('<')[0]
            remaining = msg.split('<')[1].split(',')[0]
        msg = {'gauge': gauge / 100., 'progress': progress, 'elapsed': elapsed, 'remaining': remaining}
        pub.sendMessage("progress_update", msg=msg)
