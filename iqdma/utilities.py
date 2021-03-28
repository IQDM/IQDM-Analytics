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
import numpy as np
from os import environ
import sys
from iqdma.paths import WIN_FRAME_ICON
from iqdma.utilities_dvha_stats import apply_dtype, is_numeric
from dateutil.parser import parse as date_parser
from datetime import datetime
import logging

if environ.get("READTHEDOCS") == "True" or "sphinx" in sys.prefix:
    ERR_DLG_FLAGS = None
    MSG_DLG_FLAGS = None
else:
    ERR_DLG_FLAGS = wx.ICON_ERROR | wx.OK | wx.OK_DEFAULT | wx.CENTER
    MSG_DLG_FLAGS = wx.ICON_WARNING | wx.YES | wx.NO | wx.NO_DEFAULT


logger = logging.getLogger("iqdma")


def push_to_log(exception=None, msg=None, msg_type="warning"):
    if exception is None:
        text = str(msg)
    else:
        text = (
            "%s\n%s" % (msg, exception) if msg is not None else str(exception)
        )
    func = getattr(logger, msg_type)
    func(text)


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


def set_icon(frame, icon=WIN_FRAME_ICON):
    """

    Parameters
    ----------
    frame :


    Returns
    -------

    """
    if not is_mac():
        frame.SetIcon(wx.Icon(icon))


def get_selected_listctrl_items(list_control) -> list:
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


def main_is_frozen():
    # https://pyinstaller.readthedocs.io/en/stable/runtime-information.html
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def widen_data(
    data_dict,
    uid_columns,
    x_data_cols,
    y_data_col,
    date_col=None,
    date_col_file_creation=None,
    sort_by_date=True,
    remove_partial_columns=False,
    multi_val_policy="first",
    dtype=None,
    date_parser_kwargs=None,
    verbose=False,
):
    """Convert a narrow data dictionary into wide format (i.e., from one row
    per dependent value to one row per observation)

    Parameters
    ----------
    data_dict : dict
        Data to be converted. The length of each array must be uniform.
    uid_columns : list
        Keys of data_dict used to create an observation uid
    x_data_cols : list
        Keys of columns representing independent data
    y_data_col : int, str
        Key of data_dict representing dependent data
    date_col : int, str, optional
        Key of date column
    date_col_file_creation : int, str, optional
        key of a backup date column if date_col fails, for sorting only
    sort_by_date : bool, optional
        Sort output by date (date_col required)
    remove_partial_columns : bool, optional
        If true, any columns that have a blank row will be removed
    multi_val_policy : str
        Either 'first', 'last', 'min', 'max'. If multiple values are found for
        a particular combination of x_data_cols, one value will be selected
        based on this policy.
    dtype : function
        python reserved types, e.g., int, float, str, etc. However, dtype
        could be any callable that raises a ValueError on failure.
    date_parser_kwargs : dict, optional
        Keyword arguments to be passed into dateutil.parser.parse
    verbose : bool
        Print warning about multiple values found for same uid

    Returns
    ----------
    dict
        data_dict reformatted to one row per UID
    """

    data_lengths = [len(col) for col in data_dict.values()]
    if len(set(data_lengths)) != 1:
        msg = "Each column of data_dict must be of the same length"
        raise NotImplementedError(msg)

    if multi_val_policy not in {"first", "last", "min", "mean", "max"}:
        msg = "multi_val_policy must be in 'first', 'last', 'min', 'mean', or 'max'"
        raise NotImplementedError(msg)

    data = {}
    timestamps = {}
    for row in range(len(data_dict[y_data_col])):
        uid = " && ".join([str(data_dict[col][row]) for col in uid_columns])

        if uid not in list(data):
            data[uid] = {}
            timestamps[uid] = {}

        vals = [data_dict[col][row] for col in x_data_cols]
        vals = [float(v) if is_numeric(v) else v for v in vals]
        params = " && ".join([str(v) for v in vals])

        date = 0 if date_col is None else data_dict[date_col][row]
        if date not in data[uid].keys():
            data[uid][date] = {}
            timestamps[uid][date] = {}

        if params not in list(data[uid][date]):
            data[uid][date][params] = []
            timestamps[uid][date][params] = []

        data[uid][date][params].append(data_dict[y_data_col][row])
        if date_col_file_creation:
            if date_col_file_creation in data_dict:
                timestamp = data_dict[date_col_file_creation][row]
                try:
                    timestamp = float(data_dict[date_col_file_creation][row])
                except ValueError:
                    pass
                timestamps[uid][date][params].append(timestamp)
            else:
                timestamps[uid][date][params].append(str(datetime.now()))

    x_variables = []
    for results in data.values():
        for date_results in results.values():
            for param in date_results.keys():
                if param not in {"uid", "date"}:
                    x_variables.append(param)
    x_variables = sorted(list(set(x_variables)))

    keys = ["uid", "date"] + x_variables
    if date_col_file_creation and date_col_file_creation not in keys:
        keys.append(date_col_file_creation)
    wide_data = {key: [] for key in keys}
    partial_cols = []
    for uid, date_data in data.items():
        for date, param_data in date_data.items():
            wide_data["uid"].append(uid)
            wide_data["date"].append(date)

            for x in x_variables:
                values = param_data.get(x)
                if values is None:
                    if remove_partial_columns:
                        partial_cols.append(x)
                    values = [""]

                if dtype is not None:
                    values = [apply_dtype(v, dtype) for v in values]

                value = values[0]
                if len(values) > 1:
                    if verbose:
                        print(
                            "WARNING: Multiple values found for uid: %s, "
                            "date: %s, param: %s. Only the %s value is "
                            "included in widen_data output."
                            % (uid, date, x, multi_val_policy)
                        )
                    if multi_val_policy in {"first", "last"}:
                        if date_col_file_creation:
                            param_timestamps = timestamps[uid][date][x]
                            method = {"first": "argmin", "last": "argmax"}[
                                multi_val_policy
                            ]
                            value = values[
                                getattr(np, method)(param_timestamps)
                            ]
                        elif multi_val_policy == "last":
                            value = values[-1]
                    elif multi_val_policy in {"min", "max", "mean"}:
                        try:
                            value = getattr(np, multi_val_policy)(values)
                        except Exception as e:
                            msg = (
                                f"Multivalue policy {multi_val_policy} "
                                f"failed for {uid}"
                            )
                            push_to_log(e, msg=msg)
                            value = np.nan

                wide_data[x].append(value)

    if remove_partial_columns:
        partial_cols = set(partial_cols)
        if len(partial_cols):
            for col in partial_cols:
                wide_data.pop(col)
                x_variables.pop(x_variables.index(col))

    if date_col is None:
        wide_data.pop("date")
    elif sort_by_date:
        kwargs = {} if date_parser_kwargs is None else date_parser_kwargs
        dates = [get_datetime(date, kwargs) for date in wide_data["date"]]
        for d, date_backup in enumerate(wide_data[date_col_file_creation]):
            if isinstance(dates[d], str):
                dates[d] = get_datetime(date_backup)
        sorted_indices = get_sorted_indices(dates)
        final_data = {key: [] for key in wide_data.keys()}
        for row in range(len(wide_data[x_variables[0]])):
            final_data["uid"].append(wide_data["uid"][sorted_indices[row]])
            final_data["date"].append(wide_data["date"][sorted_indices[row]])
            for x in x_variables:
                if x != date_col_file_creation:
                    final_data[x].append(wide_data[x][sorted_indices[row]])
        if date_col_file_creation in final_data.keys():
            final_data.pop(date_col_file_creation)
        return final_data

    return wide_data


def get_datetime(date, date_parser_kwargs=None):
    """Convert ``date`` to datetime

    Parameters
    ----------
    date : float, str
        Either a date time stamp (float) or a parse-able date string
    date_parser_kwargs : dict, optional
        Keyword arguments to be passed into dateutil.parser.parse

    """
    try:
        return datetime.fromtimestamp(float(date))
    except ValueError:
        kwargs = {} if date_parser_kwargs is None else date_parser_kwargs
        try:
            return date_parser(date, **kwargs)
        except Exception as e:
            msg = f"get_datetime failed on date_parser with {date}"
            push_to_log(e, msg=msg)
    except Exception as e:
        msg = f"get_datetime failed on datetime.fromtimestamp with {date}"
        push_to_log(e, msg=msg)
    return date
