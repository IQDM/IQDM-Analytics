#!/usr/bin/env python
# -*- coding: utf-8 -*-

# options.py
"""
Class used to manage user options
"""
# Copyright (c) 2016-2019 Dan Cutright
# This file is part of DVH Analytics, released under a BSD license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/cutright/DVH-Analytics

import pickle
from os.path import isfile
from os import unlink
import hashlib
from iqdma.paths import OPTIONS_PATH, OPTIONS_CHECKSUM_PATH
from iqdma._version import __version__
from iqdma.utilities import (
    MessageDialog,
    is_windows,
    set_msw_background_color,
    set_frame_icon,
)
import wx
import wx.html2 as webview
import matplotlib.colors as plot_colors


class DefaultOptions:
    """Create default options, to be inherited by Options class"""

    def __init__(self):
        self.VERSION = __version__
        self.is_edited = False

        self.MIN_BORDER = 50

        # These colors propagate to all tabs that visualize your two groups
        self.PLOT_COLOR = "blue"

        # Adjust the plot font sizes
        self.PLOT_AXIS_LABEL_FONT_SIZE = "12pt"
        self.PLOT_AXIS_MAJOR_LABEL_FONT_SIZE = "10pt"

        # Grid line properties
        self.GRID_LINE_COLOR = "lightgrey"
        self.GRID_LINE_WIDTH = 1
        self.GRID_ALPHA = 1.0

        # Number of data points are reduced by this factor during dynamic
        # plot interaction to speed-up visualizations
        # This is only applied to the DVH plot since it has a large amount
        # of data
        self.LOD_FACTOR = 100

        # Options for the time-series plot
        self.CONTROL_CHART_CIRCLE_SIZE = 10
        self.CONTROL_CHART_CIRCLE_ALPHA = 0.5
        self.CONTROL_CHART_LINE_WIDTH = 1
        self.CONTROL_CHART_LINE_DASH = "solid"
        self.CONTROL_CHART_LINE_COLOR = "black"
        self.CONTROL_CHART_CENTER_LINE_WIDTH = 2
        self.CONTROL_CHART_CENTER_LINE_DASH = "solid"
        self.CONTROL_CHART_CENTER_LINE_COLOR = "black"
        self.CONTROL_CHART_CENTER_LINE_ALPHA = 1
        self.CONTROL_CHART_UCL_LINE_WIDTH = 2
        self.CONTROL_CHART_UCL_LINE_DASH = "dashed"
        self.CONTROL_CHART_UCL_LINE_COLOR = "red"
        self.CONTROL_CHART_UCL_LINE_ALPHA = 1
        self.CONTROL_CHART_LCL_LINE_WIDTH = 2
        self.CONTROL_CHART_LCL_LINE_DASH = "dashed"
        self.CONTROL_CHART_LCL_LINE_COLOR = "red"
        self.CONTROL_CHART_LCL_LINE_ALPHA = 1
        self.CONTROL_CHART_PATCH_ALPHA = 0.2
        self.CONTROL_CHART_PATCH_COLOR = "grey"
        self.CONTROL_CHART_OUT_OF_CONTROL_COLOR = "red"
        self.CONTROL_CHART_OUT_OF_CONTROL_ALPHA = 0.8

        self.save_fig_param = {
            "figure": {
                "y_range_start": -0.0005,
                "x_range_start": 0.0,
                "y_range_end": 1.0005,
                "x_range_end": 10000.0,
                "background_fill_color": "none",
                "border_fill_color": "none",
                "plot_height": 600,
                "plot_width": 820,
            },
            "legend": {
                "background_fill_color": "white",
                "background_fill_alpha": 1.0,
                "border_line_color": "white",
                "border_line_alpha": 1.0,
                "border_line_width": 1,
            },
        }
        self.apply_range_edits = False

        self.positions = {
            "user_settings": None,
            "export_figure": None,
            "main": None,
        }
        self.window_sizes = {"main": None, "import": None}

        self.MIN_RESOLUTION_MAIN = (800, 800)
        self.MAX_INIT_RESOLUTION_MAIN = (1550, 900)

        self.ENABLE_EDGE_BACKEND = False

        self.PDF_N_JOBS = 4
        self.PDF_IGNORE_EXT = False


class Options(DefaultOptions):
    def __init__(self):
        DefaultOptions.__init__(self)
        self.__set_option_attr()

        self.load()

    def __set_option_attr(self):
        option_attr = []
        for attr in self.__dict__:
            if not attr.startswith("_"):
                option_attr.append(attr)
        self.option_attr = option_attr

    def load(self):
        self.is_edited = False
        if isfile(OPTIONS_PATH) and self.is_options_file_valid:
            try:
                with open(OPTIONS_PATH, "rb") as infile:
                    loaded_options = pickle.load(infile)
                self.upgrade_options(loaded_options)
            except Exception as e:
                print(
                    "Options.load: Options file corrupted. Loading "
                    "default options."
                )
                print(e)
                loaded_options = {}

            for key, value in loaded_options.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def save(self):
        self.is_edited = False
        out_options = {}
        for attr in self.option_attr:
            out_options[attr] = getattr(self, attr)
        out_options["VERSION"] = DefaultOptions().VERSION
        with open(OPTIONS_PATH, "wb") as outfile:
            pickle.dump(out_options, outfile)
        self.save_checksum()

    def set_option(self, attr, value):
        """
        Change or create an option value
        :param attr: name of option
        :type attr: str
        :param value: value of option
        """
        if not hasattr(self, attr):
            print("Options.set_option: %s did not previously exist" % attr)

        setattr(self, attr, value)
        self.is_edited = True

    def save_checksum(self):
        check_sum = self.calculate_checksum()
        if check_sum:
            with open(OPTIONS_CHECKSUM_PATH, "w") as outfile:
                outfile.write(check_sum)

    @staticmethod
    def calculate_checksum():
        if isfile(OPTIONS_PATH):
            with open(OPTIONS_PATH, "rb") as infile:
                options_str = str(infile.read())
            return hashlib.md5(options_str.encode("utf-8")).hexdigest()
        return None

    @staticmethod
    def load_stored_checksum():
        if isfile(OPTIONS_CHECKSUM_PATH):
            with open(OPTIONS_CHECKSUM_PATH, "r") as infile:
                checksum = infile.read()
            return checksum
        return None

    @property
    def is_options_file_valid(self):
        try:
            current_checksum = self.calculate_checksum()
            stored_checksum = self.load_stored_checksum()
            if current_checksum == stored_checksum:
                return True
        except Exception as e:
            print(
                "Options.is_options_file_valid: Corrupted options file "
                "detected. Loading default options."
            )
            print(e)
            return False

    def restore_defaults(self):
        """Delete the store options file and checksum, load defaults"""
        if isfile(OPTIONS_PATH):
            unlink(OPTIONS_PATH)
        if isfile(OPTIONS_CHECKSUM_PATH):
            unlink(OPTIONS_CHECKSUM_PATH)
        default_options = DefaultOptions()

        for attr in default_options.__dict__:
            if not attr.startswith("_"):
                setattr(self, attr, getattr(default_options, attr))

    def clear_positions(self, *evt):
        """Clear all stored window positions, may be useful if window is
        off screen on Show"""
        self.positions = {key: None for key in list(self.positions)}

    def clear_window_sizes(self, *evt):
        """Clear all stored window sizes, may be useful if window is
        off screen on Show"""
        self.window_sizes = {key: None for key in list(self.window_sizes)}

    def apply_window_position(self, frame, position_key):
        """Given a frame, set to previously stored position or center it"""
        if self.positions[position_key] is not None:
            frame.SetPosition(self.positions[position_key])
        else:
            frame.Center()

    def set_window_size(self, frame, size_key):
        if size_key in self.window_sizes.keys():
            self.window_sizes[size_key] = frame.GetSize()

    def save_window_position(self, frame, position_key):
        """Store the position of the provided frame"""
        self.positions[position_key] = frame.GetPosition()

    def upgrade_options(self, loaded_options):
        """Reserve this space to apply all option file upgrades"""
        # This method is only needed for options that change type or structure
        # New options using a new attribute name will be automatically
        # generated by the DefaultOptions class
        pass


class UserSettings(wx.Frame):
    """
    Customize directories and visual settings for DVHA
    """

    def __init__(self, parent):
        """
        :param parent: main application frame
        """
        wx.Frame.__init__(self, None, title="User Settings")

        self.is_edge_backend_available = None
        try:
            self.is_edge_backend_available = (
                webview.WebView.IsBackendAvailable(webview.WebViewBackendEdge)
            )
        except Exception:
            self.is_edge_backend_available = False

        self.parent = parent
        self.options = parent.options
        self.options.edit_detected = False

        colors = list(plot_colors.cnames)
        colors.sort()

        color_variables = self.get_option_choices("COLOR")
        size_variables = self.get_option_choices("SIZE")
        width_variables = self.get_option_choices("LINE_WIDTH")
        line_dash_variables = self.get_option_choices("LINE_DASH")
        alpha_variables = self.get_option_choices("ALPHA")

        line_style_options = [
            "solid",
            "dashed",
            "dotted",
            "dotdash",
            "dashdot",
        ]

        # self.SetSize((500, 580))
        self.combo_box_colors_category = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=color_variables,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.combo_box_colors_selection = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=colors,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.combo_box_sizes_category = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=size_variables,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.spin_ctrl_sizes_input = wx.SpinCtrl(
            self, wx.ID_ANY, "0", min=0, max=20, style=wx.SP_ARROW_KEYS
        )
        self.combo_box_line_widths_category = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=width_variables,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.spin_ctrl_line_widths_input = wx.SpinCtrl(
            self, wx.ID_ANY, "0", min=0, max=10, style=wx.SP_ARROW_KEYS
        )
        self.combo_box_line_styles_category = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=line_dash_variables,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.combo_box_line_styles_selection = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=line_style_options,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.combo_box_alpha_category = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=alpha_variables,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.spin_ctrl_alpha_input = wx.SpinCtrlDouble(
            self,
            wx.ID_ANY,
            "0",
            min=0,
            max=1.0,
            style=wx.SP_ARROW_KEYS,
            inc=0.1,
        )

        self.spin_ctrl_n_jobs = wx.SpinCtrl(
            self, wx.ID_ANY, "1", min=1, max=16, style=wx.SP_ARROW_KEYS
        )
        self.combo_box_pdf_ext = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=["Yes", "No"],
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )

        if is_windows():
            self.checkbox_edge_backend = wx.CheckBox(
                self, wx.ID_ANY, "Enable Edge WebView Backend"
            )
            if not self.is_edge_backend_available:
                self.checkbox_edge_backend.Disable()

        self.button_restore_defaults = wx.Button(
            self, wx.ID_ANY, "Restore Defaults"
        )
        self.button_ok = wx.Button(self, wx.ID_OK, "OK")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.button_apply = wx.Button(self, wx.ID_ANY, "Apply")

        self.__set_properties()
        self.__do_layout()
        self.__do_bind()

        self.refresh_options()

        self.is_edited = False

        set_msw_background_color(self)
        set_frame_icon(self)

    def __set_properties(self):
        self.combo_box_colors_category.SetMinSize(
            (250, self.combo_box_colors_category.GetSize()[1])
        )
        self.combo_box_colors_selection.SetMinSize(
            (145, self.combo_box_colors_selection.GetSize()[1])
        )
        self.combo_box_sizes_category.SetMinSize(
            (250, self.combo_box_sizes_category.GetSize()[1])
        )
        self.spin_ctrl_sizes_input.SetMinSize((50, 22))
        self.combo_box_line_widths_category.SetMinSize(
            (250, self.combo_box_line_widths_category.GetSize()[1])
        )
        self.spin_ctrl_line_widths_input.SetMinSize((50, 22))
        self.combo_box_line_styles_category.SetMinSize(
            (250, self.combo_box_line_styles_category.GetSize()[1])
        )
        self.combo_box_line_styles_selection.SetMinSize(
            (145, self.combo_box_line_styles_selection.GetSize()[1])
        )
        self.combo_box_alpha_category.SetMinSize(
            (250, self.combo_box_alpha_category.GetSize()[1])
        )
        self.spin_ctrl_alpha_input.SetMinSize((70, 22))

        self.spin_ctrl_n_jobs.SetMinSize((50, 22))
        self.combo_box_pdf_ext.SetMinSize(
            (80, self.combo_box_pdf_ext.GetSize()[1])
        )

        self.spin_ctrl_alpha_input.SetIncrement(0.1)

        # Windows needs this done explicitly or the value will be an empty string
        self.combo_box_alpha_category.SetValue("Control Chart Circle Alpha")
        self.combo_box_colors_category.SetValue("Plot Color")
        self.combo_box_line_styles_category.SetValue("Control Chart Center Line Dash")
        self.combo_box_line_widths_category.SetValue(
            "Control Chart Center Line Width"
        )
        self.combo_box_sizes_category.SetValue("Plot Axis Label Font Size")

        if is_windows():
            self.checkbox_edge_backend.SetValue(
                self.options.ENABLE_EDGE_BACKEND
            )
            self.checkbox_edge_backend.SetToolTip(
                "Allows for more complete plot interaction. Must restart DVHA for "
                "change to be applied. If you cannot toggle this checkbox, "
                "Edge is not availabe. Requires MS Edge Beta to be installed: "
                "https://www.microsoftedgeinsider.com/en-us/download"
            )
        self.combo_box_pdf_ext.SetValue("No" if self.options.PDF_IGNORE_EXT else "Yes")

    def __do_layout(self):
        sizer_wrapper = wx.BoxSizer(wx.VERTICAL)
        sizer_ok_cancel = wx.BoxSizer(wx.HORIZONTAL)
        sizer_plot_options = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Plot Options"), wx.VERTICAL
        )
        sizer_iqdm_pdf_options = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "IQDM PDF Options"), wx.VERTICAL
        )
        sizer_alpha = wx.BoxSizer(wx.VERTICAL)
        sizer_alpha_input = wx.BoxSizer(wx.HORIZONTAL)
        sizer_line_styles = wx.BoxSizer(wx.VERTICAL)
        sizer_line_styles_input = wx.BoxSizer(wx.HORIZONTAL)
        sizer_line_widths = wx.BoxSizer(wx.VERTICAL)
        sizer_line_widths_input = wx.BoxSizer(wx.HORIZONTAL)
        sizer_sizes = wx.BoxSizer(wx.VERTICAL)
        sizer_sizes_input = wx.BoxSizer(wx.HORIZONTAL)
        sizer_colors = wx.BoxSizer(wx.VERTICAL)
        sizer_colors_input = wx.BoxSizer(wx.HORIZONTAL)
        sizer_n_jobs = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pdf_ext = wx.BoxSizer(wx.HORIZONTAL)

        label_colors = wx.StaticText(self, wx.ID_ANY, "Colors:")
        sizer_colors.Add(label_colors, 0, 0, 0)
        sizer_colors_input.Add(self.combo_box_colors_category, 0, 0, 0)
        sizer_colors_input.Add((20, 20), 0, 0, 0)
        sizer_colors_input.Add(self.combo_box_colors_selection, 0, 0, 0)
        sizer_colors.Add(sizer_colors_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_colors, 1, wx.EXPAND, 0)

        label_sizes = wx.StaticText(self, wx.ID_ANY, "Sizes:")
        sizer_sizes.Add(label_sizes, 0, 0, 0)
        sizer_sizes_input.Add(self.combo_box_sizes_category, 0, 0, 0)
        sizer_sizes_input.Add((20, 20), 0, 0, 0)
        sizer_sizes_input.Add(self.spin_ctrl_sizes_input, 0, 0, 0)
        sizer_sizes.Add(sizer_sizes_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_sizes, 1, wx.EXPAND, 0)

        label_line_widths = wx.StaticText(self, wx.ID_ANY, "Line Widths:")
        sizer_line_widths.Add(label_line_widths, 0, 0, 0)
        sizer_line_widths_input.Add(
            self.combo_box_line_widths_category, 0, 0, 0
        )
        sizer_line_widths_input.Add((20, 20), 0, 0, 0)
        sizer_line_widths_input.Add(self.spin_ctrl_line_widths_input, 0, 0, 0)
        sizer_line_widths.Add(sizer_line_widths_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_line_widths, 1, wx.EXPAND, 0)

        label_line_styles = wx.StaticText(self, wx.ID_ANY, "Line Styles:")
        sizer_line_styles.Add(label_line_styles, 0, 0, 0)
        sizer_line_styles_input.Add(
            self.combo_box_line_styles_category, 0, 0, 0
        )
        sizer_line_styles_input.Add((20, 20), 0, 0, 0)
        sizer_line_styles_input.Add(
            self.combo_box_line_styles_selection, 0, 0, 0
        )
        sizer_line_styles.Add(sizer_line_styles_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_line_styles, 1, wx.EXPAND, 0)

        label_alpha = wx.StaticText(self, wx.ID_ANY, "Alpha:")
        sizer_alpha.Add(label_alpha, 0, 0, 0)
        sizer_alpha_input.Add(self.combo_box_alpha_category, 0, 0, 0)
        sizer_alpha_input.Add((20, 20), 0, 0, 0)
        sizer_alpha_input.Add(self.spin_ctrl_alpha_input, 0, 0, 0)
        sizer_alpha.Add(sizer_alpha_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_alpha, 1, wx.EXPAND, 0)
        if is_windows():
            sizer_plot_options.Add(
                self.checkbox_edge_backend, 0, wx.EXPAND | wx.TOP, 5
            )
        sizer_wrapper.Add(
            sizer_plot_options, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10
        )

        label_n_jobs = wx.StaticText(self, wx.ID_ANY, "Multi-Threading Jobs:")
        sizer_n_jobs.Add(label_n_jobs, 0, 0, 0)
        sizer_n_jobs.Add((20, 20), 0, 0, 0)
        sizer_n_jobs.Add(self.spin_ctrl_n_jobs, 0, 0, 0)
        sizer_iqdm_pdf_options.Add(sizer_n_jobs, 0, wx.EXPAND, 0)

        label_ext = wx.StaticText(self, wx.ID_ANY, "Analyze .pdf only:")
        sizer_pdf_ext.Add(label_ext, 0, 0, 0)
        sizer_pdf_ext.Add((20, 20), 0, 0, 0)
        sizer_pdf_ext.Add(self.combo_box_pdf_ext, 0, 0, 0)
        sizer_iqdm_pdf_options.Add(sizer_pdf_ext, 0, wx.EXPAND, 0)
        sizer_wrapper.Add(
            sizer_iqdm_pdf_options, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            10
        )

        sizer_ok_cancel.Add(self.button_restore_defaults, 0, wx.RIGHT, 20)
        sizer_ok_cancel.Add(self.button_apply, 0, wx.LEFT | wx.RIGHT, 5)
        sizer_ok_cancel.Add(self.button_ok, 0, wx.LEFT | wx.RIGHT, 5)
        sizer_ok_cancel.Add(self.button_cancel, 0, wx.LEFT | wx.RIGHT, 5)
        sizer_wrapper.Add(sizer_ok_cancel, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(sizer_wrapper)
        self.Layout()
        self.Fit()

        self.options.apply_window_position(self, "user_settings")

    def __do_bind(self):
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_input_colors_var,
            id=self.combo_box_colors_category.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_size_var,
            id=self.combo_box_sizes_category.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_line_width_var,
            id=self.combo_box_line_widths_category.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_line_style_var,
            id=self.combo_box_line_styles_category.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_alpha_var,
            id=self.combo_box_alpha_category.GetId(),
        )

        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_input_colors_val,
            id=self.combo_box_colors_selection.GetId(),
        )
        self.Bind(
            wx.EVT_TEXT,
            self.update_size_val,
            id=self.spin_ctrl_sizes_input.GetId(),
        )
        self.Bind(
            wx.EVT_TEXT,
            self.update_line_width_val,
            id=self.spin_ctrl_line_widths_input.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_line_style_val,
            id=self.combo_box_line_styles_selection.GetId(),
        )
        self.Bind(
            wx.EVT_TEXT,
            self.update_alpha_val,
            id=self.spin_ctrl_alpha_input.GetId(),
        )
        if is_windows() and self.is_edge_backend_available:
            self.Bind(
                wx.EVT_CHECKBOX,
                self.on_enable_edge,
                id=self.checkbox_edge_backend.GetId(),
            )

        self.Bind(
            wx.EVT_TEXT,
            self.update_n_jobs_val,
            id=self.spin_ctrl_n_jobs.GetId(),
        )
        self.Bind(
            wx.EVT_TEXT,
            self.update_pdf_ext_val,
            id=self.combo_box_pdf_ext.GetId(),
        )

        self.Bind(
            wx.EVT_BUTTON,
            self.restore_defaults,
            id=self.button_restore_defaults.GetId(),
        )
        self.Bind(wx.EVT_BUTTON, self.on_apply, id=self.button_apply.GetId())
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)

        self.Bind(wx.EVT_CLOSE, self.on_cancel)

    def on_ok(self, *evt):
        if self.options.is_edited:  # Tracks edits since last redraw
            self.apply_and_redraw_plots()
        self.close()

    def on_cancel(self, *evt):
        self.options.load()
        if self.is_edited:  # Tracks edits since last options save
            self.apply_and_redraw_plots()
        self.close()

    def close(self, *evt):
        self.save_window_position()
        self.options.save()
        self.parent.user_settings = None
        self.Destroy()

    def save_window_position(self):
        self.options.save_window_position(self, "user_settings")

    def get_option_choices(self, category):
        """
        Lookup properties in Options.option_attr that fit the specified category
        :param category: COLOR, SIZE, ALPHA, LINE_WIDTH, LINE_DASH
        :type category: str
        :return: all options with the category in their name
        :rtype: list
        """
        choices = [
            self.clean_option_variable(c)
            for c in self.options.option_attr
            if c.find(category) > -1
        ]
        choices.sort()
        return choices

    @staticmethod
    def clean_option_variable(option_variable, inverse=False):
        """
        Convert option variable between UI and python format
        :param option_variable: option available for edit user settings UI
        :type option_variable: str
        :param inverse: True to return python format, False to return UI format
        :type inverse: bool
        :return: formatted option variable
        :rtype: str
        """
        if inverse:
            return option_variable.upper().replace(" ", "_")
        else:
            return (
                option_variable.replace("_", " ")
                .title()
                .replace("Dvh", "DVH")
                .replace("Iqr", "IQR")
            )

    def update_input_colors_var(self, *args):
        var = self.clean_option_variable(
            self.combo_box_colors_category.GetValue(), inverse=True
        )
        val = getattr(self.options, var)
        self.combo_box_colors_selection.SetValue(val)

    def update_input_colors_val(self, *args):
        var = self.clean_option_variable(
            self.combo_box_colors_category.GetValue(), inverse=True
        )
        val = self.combo_box_colors_selection.GetValue()
        self.options.set_option(var, val)

    def update_size_var(self, *args):
        var = self.clean_option_variable(
            self.combo_box_sizes_category.GetValue(), inverse=True
        )
        try:
            val = getattr(self.options, var).replace("pt", "")
        except AttributeError:
            val = str(getattr(self.options, var))
        try:
            val = int(float(val))
        except ValueError:
            pass
        self.spin_ctrl_sizes_input.SetValue(val)

    def update_size_val(self, *args):
        new = self.spin_ctrl_sizes_input.GetValue()
        if "Font" in self.combo_box_sizes_category.GetValue():
            try:
                val = str(int(new)) + "pt"
            except ValueError:
                val = "10pt"
        else:
            try:
                val = float(new)
            except ValueError:
                val = 1.0

        var = self.clean_option_variable(
            self.combo_box_sizes_category.GetValue(), inverse=True
        )
        self.options.set_option(var, val)

    def update_n_jobs_var(self, *args):
        self.spin_ctrl_n_jobs.SetValue(self.options.PDF_N_JOBS)

    def update_n_jobs_val(self, *args):
        new = self.spin_ctrl_n_jobs.GetValue()
        try:
            val = int(float(new))
        except ValueError:
            val = 1
        self.options.set_option('N_JOBS', val)

    def update_pdf_ext_var(self, *args):
        val = "No" if self.options.PDF_IGNORE_EXT else "Yes"
        self.combo_box_pdf_ext.SetValue(val)

    def update_pdf_ext_val(self, *args):
        new = self.combo_box_pdf_ext.GetValue()
        self.options.set_option('N_JOBS', new == 'No')

    def update_line_width_var(self, *args):
        var = self.clean_option_variable(
            self.combo_box_line_widths_category.GetValue(), inverse=True
        )
        val = str(getattr(self.options, var))
        try:
            val = int(float(val))
        except ValueError:
            pass
        self.spin_ctrl_line_widths_input.SetValue(val)

    def update_line_width_val(self, *args):
        new = self.spin_ctrl_line_widths_input.GetValue()
        try:
            val = int(float(new))
        except ValueError:
            val = 1
        var = self.clean_option_variable(
            self.combo_box_line_widths_category.GetValue(), inverse=True
        )
        self.options.set_option(var, val)

    def update_line_style_var(self, *args):
        var = self.clean_option_variable(
            self.combo_box_line_styles_category.GetValue(), inverse=True
        )
        self.combo_box_line_styles_selection.SetValue(
            getattr(self.options, var)
        )

    def update_line_style_val(self, *args):
        var = self.clean_option_variable(
            self.combo_box_line_styles_category.GetValue(), inverse=True
        )
        val = self.combo_box_line_styles_selection.GetValue()
        self.options.set_option(var, val)

    def update_alpha_var(self, *args):
        var = self.clean_option_variable(
            self.combo_box_alpha_category.GetValue(), inverse=True
        )
        self.spin_ctrl_alpha_input.SetValue(str(getattr(self.options, var)))

    def update_alpha_val(self, *args):
        new = self.spin_ctrl_alpha_input.GetValue()
        try:
            val = float(new)
        except ValueError:
            val = 1.0
        var = self.clean_option_variable(
            self.combo_box_alpha_category.GetValue(), inverse=True
        )
        self.options.set_option(var, val)

    def refresh_options(self):
        self.update_alpha_var()
        self.update_input_colors_var()
        self.update_line_style_var()
        self.update_line_width_var()
        self.update_size_var()
        self.update_n_jobs_var()

    def restore_defaults(self, *args):
        MessageDialog(
            self,
            "Restore default preferences?",
            action_yes_func=self.options.restore_defaults,
        )
        self.update_size_val()
        self.refresh_options()
        self.on_apply()

    def on_enable_edge(self, *evt):
        self.options.set_option(
            "ENABLE_EDGE_BACKEND", self.checkbox_edge_backend.GetValue()
        )

    def on_apply(self, *evt):
        self.apply_and_redraw_plots()
        self.is_edited = True  # Used to track edits since last options save
        self.options.is_edited = False  # Used to track edits since redraw, is set to True on options.set_option()

    def apply_and_redraw_plots(self):
        self.parent.apply_plot_options()
        self.parent.redraw_plots()
