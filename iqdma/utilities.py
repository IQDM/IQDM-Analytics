#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# utilities.py
"""utilities for IQDM Analytics"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

import wx
import wx.html2 as webview
from os import environ
from sys import prefix
from iqdma.paths import WIN_APP_ICON

if environ.get("READTHEDOCS") == "True" or "sphinx" in prefix:
    ERR_DLG_FLAGS = None
    MSG_DLG_FLAGS = None
else:
    ERR_DLG_FLAGS = wx.ICON_ERROR | wx.OK | wx.OK_DEFAULT | wx.CENTER
    MSG_DLG_FLAGS = wx.ICON_WARNING | wx.YES | wx.NO | wx.NO_DEFAULT


def is_windows():
    return wx.Platform == "__WXMSW__"


def is_linux():
    return wx.Platform == "__WXGTK__"


def is_mac():
    return wx.Platform == "__WXMAC__"


class ErrorDialog:
    def __init__(self, parent, message, caption, flags=ERR_DLG_FLAGS):
        """
        This class allows error messages to be called with a one-liner else-where
        :param parent: wx parent object
        :param message: error message
        :param caption: error title
        :param flags: flags for wx.MessageDialog
        """
        self.dlg = wx.MessageDialog(parent, message, caption, flags)
        self.dlg.ShowModal()
        self.dlg.Destroy()


def save_data_to_file(
    frame,
    title,
    data,
    wildcard="CSV files (*.csv)|*.csv",
    data_type="string",
):
    """
    from https://wxpython.org/Phoenix/docs/html/wx.FileDialog.html
    :param frame: GUI parent
    :param title: title for the file dialog window
    :type title: str
    :param data: text data or pickle-able object to be written
    :param wildcard: restrict visible files and intended file extension
    :type wildcard: str
    :param data_type: either 'string' or 'pickle'
    :type data_type: str
    """

    with wx.FileDialog(
        frame,
        title,
        wildcard=wildcard,
        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
    ) as fileDialog:

        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return

        pathname = fileDialog.GetPath()

        if data_type == "string":
            try:
                with open(pathname, "w", encoding="utf-8") as file:
                    file.write(data)
            except IOError:
                wx.LogError(
                    "Cannot save current data in file '%s'." % pathname
                )

        elif data_type == "function":
            data(pathname)

        return pathname


def get_wildcards(extensions):
    """

    Parameters
    ----------
    extensions :


    Returns
    -------

    """
    if type(extensions) is not list:
        extensions = [extensions]
    return "|".join(
        ["%s (*.%s)|*.%s" % (ext.upper(), ext, ext) for ext in extensions]
    )


FIG_WILDCARDS = get_wildcards(["png", "html", "svg"])


def get_windows_webview_backend(include_edge=False):
    """Get the wx.html2 backend for MSW

    Returns
    -------
    dict
        wx.html2 backend id and name. Returns None if not MSW.
    """
    if is_windows():
        # WebView Backends
        backends = [
            (webview.WebViewBackendEdge, "WebViewBackendEdge"),
            (webview.WebViewBackendIE, "WebViewBackendIE"),
            (webview.WebViewBackendWebKit, "WebViewBackendWebKit"),
            (webview.WebViewBackendDefault, "WebViewBackendDefault"),
        ]
        if not include_edge:
            backends.pop(0)
        webview.WebView.MSWSetEmulationLevel(webview.WEBVIEWIE_EMU_IE11)
        for id, name in backends:
            if webview.WebView.IsBackendAvailable(id):
                return {"id": id, "name": name}


def scale_bitmap(bitmap, width, height):
    """Used to scale tool bar images for MSW and GTK, MAC automatically scales

    Parameters
    ----------
    bitmap :
        bitmap to be scaled
        type bitmap: Bitmap
    width : int
        width of output bitmap
    height : int
        height of output bitmap

    Returns
    -------
    Bitmap
        scaled bitmap

    """
    image = wx.Bitmap.ConvertToImage(bitmap)
    image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    return wx.Bitmap(image)


def set_frame_icon(frame):
    """

    Parameters
    ----------
    frame :


    Returns
    -------

    """
    if not is_mac():
        frame.SetIcon(wx.Icon(WIN_APP_ICON))


def get_selected_listctrl_items(list_control):
    """Get the indices of the currently selected items of a wx.ListCtrl object

    Parameters
    ----------
    list_control : ListCtrl
        any wx.ListCtrl object

    Returns
    -------
    list
        indices of selected items

    """
    selection = []

    index_current = -1
    while True:
        index_next = list_control.GetNextItem(
            index_current, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED
        )
        if index_next == -1:
            return selection

        selection.append(index_next)
        index_current = index_next


def get_sorted_indices(some_list):
    try:
        return [i[0] for i in sorted(enumerate(some_list), key=lambda x: x[1])]
    except TypeError:  # can't sort if a mix of str and float
        try:
            temp_data = [
                [value, -float("inf")][value == "None"] for value in some_list
            ]
            return [
                i[0] for i in sorted(enumerate(temp_data), key=lambda x: x[1])
            ]
        except TypeError:
            temp_data = [str(value) for value in some_list]
            return [
                i[0] for i in sorted(enumerate(temp_data), key=lambda x: x[1])
            ]


def set_msw_background_color(window_obj, color="lightgrey"):
    if is_windows():
        window_obj.SetBackgroundColour(color)


class MessageDialog:
    """This is the base class for Yes/No Dialog boxes
    Inherit this class, then over-write action_yes and action_no functions
    with appropriate behaviors
    """

    def __init__(
        self,
        parent,
        caption,
        message="Are you sure?",
        action_yes_func=None,
        action_no_func=None,
        flags=MSG_DLG_FLAGS,
    ):
        if is_windows():
            message = "\n".join([caption, message])
            caption = " "
        self.dlg = wx.MessageDialog(parent, message, caption, flags)
        self.parent = parent
        self.action_yes_func = action_yes_func
        self.action_no_func = action_no_func
        self.run()

    def run(self):
        """ """
        res = self.dlg.ShowModal()
        [self.action_no, self.action_yes][res == wx.ID_YES]()
        self.dlg.Destroy()

    def action_yes(self):
        """ """
        if self.action_yes_func is not None:
            self.action_yes_func()

    def action_no(self):
        """ """
        if self.action_no_func is not None:
            self.action_no_func()
