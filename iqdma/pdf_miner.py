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
from os.path import isdir
from iqdma.utilities import set_icon


class ProgressFrame(wx.Dialog):
    """Create a window to display progress and begin provided worker"""

    def __init__(self, parent, options):
        wx.Dialog.__init__(self, None)
        self.parent = parent
        set_icon(self)

        self.text_ctrl = {
            "scan": wx.TextCtrl(self, wx.ID_ANY, ""),
            "output": wx.TextCtrl(self, wx.ID_ANY, ""),
        }

        self.button = {
            "scan": wx.Button(self, wx.ID_ANY, "Browse"),
            "output": wx.Button(self, wx.ID_ANY, "Browse"),
            "exec": wx.Button(self, wx.ID_ANY, "Start"),
        }
        self.button["exec"].Disable()

        self.iqdm_pdf_kwargs = {
            "ignore_extension": options.PDF_IGNORE_EXT,
            "processes": options.PDF_N_JOBS,
        }

        self.gauge = wx.Gauge(self, wx.ID_ANY, 100)
        # self.gauge.Hide()
        self.label_progress = wx.StaticText(self, wx.ID_ANY, "")
        self.label_elapsed = wx.StaticText(self, wx.ID_ANY, "")
        self.label_remaining = wx.StaticText(self, wx.ID_ANY, "")

        self.__set_properties()
        self.__do_bind()
        self.__do_layout()
        self.__do_subscribe()

        self.Show()

    def __do_subscribe(self):
        pub.subscribe(self.update, "progress_update")

    def run(self):
        """Initiate layout in GUI and begin thread"""
        # self.gauge.Show()
        self.button["exec"].Disable()
        self.iqdm_pdf_kwargs["init_directory"] = self.text_ctrl[
            "scan"
        ].GetValue()
        self.iqdm_pdf_kwargs["output_dir"] = self.text_ctrl[
            "output"
        ].GetValue()

        for key in self.text_ctrl.keys():
            self.text_ctrl[key].Disable()
            self.button[key].Disable()

        self.label_progress.SetLabelText("Reading directory tree...")
        self.Layout()
        ProgressFrameWorker(self.iqdm_pdf_kwargs)

    def callback(self, msg):
        wx.CallAfter(self.gauge.SetValue, int(msg.split("%|")[0]))

    def __set_properties(self):
        self.SetMinSize((672, 100))
        self.SetTitle("IQDM-PDF")

    def __do_bind(self):
        self.Bind(wx.EVT_CLOSE, self.close)
        self.Bind(
            wx.EVT_BUTTON, self.on_browse_scan, id=self.button["scan"].GetId()
        )
        self.Bind(
            wx.EVT_BUTTON,
            self.on_browse_output,
            id=self.button["output"].GetId(),
        )
        self.Bind(
            wx.EVT_TEXT, self.enable_start, id=self.text_ctrl["scan"].GetId()
        )
        self.Bind(
            wx.EVT_TEXT, self.enable_start, id=self.text_ctrl["output"].GetId()
        )
        self.Bind(
            wx.EVT_BUTTON, self.on_button_exec, id=self.button["exec"].GetId()
        )

    def __do_layout(self):

        sizer = {
            "wrapper": wx.BoxSizer(wx.VERTICAL),
            "time": wx.BoxSizer(wx.HORIZONTAL),
            "exec": wx.BoxSizer(wx.HORIZONTAL),
        }
        static_box_sizers = {
            "scan": ("Scanning Directory", wx.HORIZONTAL),
            "output": ("Output Directory", wx.HORIZONTAL),
        }
        for key, box in static_box_sizers.items():
            sizer[key] = wx.StaticBoxSizer(
                wx.StaticBox(self, wx.ID_ANY, box[0]), box[1]
            )

        for key, text_ctrl in self.text_ctrl.items():
            sizer[key].Add(self.text_ctrl[key], 1, wx.EXPAND | wx.ALL, 5)
            sizer[key].Add(self.button[key], 0, wx.ALL, 5)
            sizer["wrapper"].Add(sizer[key], 0, wx.EXPAND | wx.ALL, 5)

        sizer["wrapper"].Add(self.label_progress, 0, wx.TOP | wx.LEFT, 10)
        sizer["wrapper"].Add(self.gauge, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        sizer["time"].Add(self.label_elapsed, 1, wx.EXPAND | wx.LEFT, 10)
        sizer["time"].Add(self.label_remaining, 0, wx.RIGHT, 10)
        sizer["wrapper"].Add(sizer["time"], 1, wx.EXPAND, 0)

        sizer["exec"].Add((20, 20), 1, wx.EXPAND, 0)
        sizer["exec"].Add(self.button["exec"], 0, wx.EXPAND | wx.ALL, 5)
        sizer["wrapper"].Add(sizer["exec"], 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer["wrapper"])
        self.Fit()
        self.Layout()
        self.Center()

    def browse(self, key, msg):
        dlg = wx.DirDialog(
            self,
            msg,
            "",
            style=wx.DD_DIR_MUST_EXIST | wx.DD_DEFAULT_STYLE,
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.text_ctrl[key].SetValue(dlg.GetPath())
        dlg.Destroy()

    def on_browse_scan(self, *evt):
        self.browse("scan", "Select a Scanning Directory")
        if not self.text_ctrl["output"].GetValue():
            self.text_ctrl["output"].SetValue(
                self.text_ctrl["scan"].GetValue()
            )

    def on_browse_output(self, *evt):
        self.browse("output", "Select an Output Directory")

    def enable_start(self, *evt):
        self.button["exec"].Enable(
            isdir(self.text_ctrl["scan"].GetValue())
            and isdir(self.text_ctrl["output"].GetValue())
        )

    def on_button_exec(self, *evt):
        if self.button["exec"].GetLabel() == "Start":
            self.run()
        else:
            self.close()

    def set_title(self, msg):
        wx.CallAfter(self.SetTitle, msg)

    def update(self, msg):
        if msg["gauge"] == 1:
            self.button["exec"].SetLabelText("Close")
            self.button["exec"].Enable()
        progress = f"Processing File: {msg['progress']}"
        elapsed = f"Elapsed: {msg['elapsed']}"
        remaining = f"Est. Remaining: {msg['remaining']}"
        if msg["progress"]:
            wx.CallAfter(self.label_progress.SetLabelText, progress)
        elif msg["gauge"] == 1:
            label = self.label_progress.GetLabel()
            if "/" in label:
                count = self.label_progress.GetLabel().split("/")[1]
                label = f"COMPLETE: Processed {count} file(s)"
            else:
                label = "COMPLETE"
            wx.CallAfter(self.label_progress.SetLabelText, label)
            wx.CallAfter(self.label_remaining.SetLabelText, "")
        if msg["elapsed"]:
            wx.CallAfter(self.label_elapsed.SetLabelText, elapsed)
        if msg["remaining"]:
            wx.CallAfter(self.label_remaining.SetLabelText, remaining)
        wx.CallAfter(self.gauge.SetValue, int(100 * msg["gauge"]))
        wx.CallAfter(self.Layout)

    def close(self, *evt):
        pub.unsubAll(topicName="progress_update")
        self.parent.pdf_miner_window = None
        wx.CallAfter(self.Destroy)


class ProgressFrameWorker(Thread):
    """Create a thread, perform action on each item in obj_list"""

    def __init__(self, iqdm_pdf_kwargs):
        Thread.__init__(self)
        self.iqdm_pdf_kwargs = iqdm_pdf_kwargs
        self.iqdm_pdf_kwargs["callback"] = self.callback
        self.start()

    def run(self):
        process_files(**self.iqdm_pdf_kwargs)

    @staticmethod
    def callback(msg):
        gauge = 100 if msg == "complete" else int(msg.split("%|")[0])
        if msg == "complete":
            progress = elapsed = remaining = ""
        else:
            progress = msg.split("| ")[1].split(" ")[0]
            elapsed = msg.split("[")[1].split("<")[0]
            remaining = msg.split("<")[1].split(",")[0]
        msg = {
            "gauge": gauge / 100.0,
            "progress": progress,
            "elapsed": elapsed,
            "remaining": remaining,
        }
        pub.sendMessage("progress_update", msg=msg)
