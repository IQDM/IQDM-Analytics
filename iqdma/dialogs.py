#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dialogs.py
"""secondary windows for IQDM Analytics"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

from os.path import basename
from iqdma.paths import LICENSE_PATH
from iqdma.options import DefaultOptions, MATPLOTLIB_COLORS
from iqdma.utilities import (
    MessageDialog,
    is_windows,
    set_msw_background_color,
    set_icon,
)
import wx
import wx.html2 as webview
from iqdma.importer import import_csv_templates, create_default_parsers


class About(wx.Dialog):
    """Simple dialog to display the LICENSE file and a brief text header in a
    scrollable window
    """

    def __init__(self, *evt):
        wx.Dialog.__init__(self, None, title="About IQDM Analytics")
        set_icon(self)

        scrolled_window = wx.ScrolledWindow(self, wx.ID_ANY)

        with open(LICENSE_PATH, "r", encoding="utf8") as license_file:
            license_text = "".join([line for line in license_file])

        license_text = (
            "IQDM Analytics v%s\nhttps://github.com/IQDM/IQDM-Analytics\n\n%s"
            % (
                DefaultOptions().VERSION,
                license_text,
            )
        )

        sizer_wrapper = wx.BoxSizer(wx.VERTICAL)
        sizer_text = wx.BoxSizer(wx.VERTICAL)

        scrolled_window.SetScrollRate(20, 20)

        license_text = wx.StaticText(scrolled_window, wx.ID_ANY, license_text)
        sizer_text.Add(license_text, 0, wx.EXPAND | wx.ALL, 5)
        scrolled_window.SetSizer(sizer_text)
        sizer_wrapper.Add(scrolled_window, 1, wx.EXPAND, 0)

        self.SetBackgroundColour(wx.WHITE)

        self.SetSizer(sizer_wrapper)
        self.SetSize((750, 900))
        self.Center()

        self.ShowModal()
        self.Destroy()


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
        self.reimport_required = False
        try:
            self.is_edge_backend_available = (
                webview.WebView.IsBackendAvailable(webview.WebViewBackendEdge)
            )
        except Exception:
            self.is_edge_backend_available = False

        self.parent = parent
        self.options = parent.options
        self.options.edit_detected = False

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
            choices=MATPLOTLIB_COLORS,
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
        self.spin_ctrl_cc_std_dev = wx.SpinCtrlDouble(
            self,
            wx.ID_ANY,
            "0",
            min=0.1,
            max=10.0,
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
        self.combo_box_duplicates = wx.ComboBox(
            self,
            wx.ID_ANY,
            choices=DefaultOptions().DUPLICATE_VALUE_OPTIONS,
            style=wx.CB_DROPDOWN | wx.CB_READONLY,
        )
        self.checkbox_duplicates = wx.CheckBox(
            self, wx.ID_ANY, "Enable Duplicate Detection"
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
        set_icon(self)

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
        self.spin_ctrl_cc_std_dev.SetMinSize((70, 22))

        self.spin_ctrl_n_jobs.SetMinSize((50, 22))
        self.combo_box_pdf_ext.SetMinSize(
            (80, self.combo_box_pdf_ext.GetSize()[1])
        )
        self.combo_box_duplicates.SetMinSize(
            (80, self.combo_box_duplicates.GetSize()[1])
        )

        self.spin_ctrl_alpha_input.SetIncrement(0.1)
        self.spin_ctrl_cc_std_dev.SetIncrement(0.1)

        # Windows needs this done explicitly or the value will be an empty string
        self.combo_box_alpha_category.SetValue("Control Chart Circle Alpha")
        self.combo_box_colors_category.SetValue("Plot Color")
        self.combo_box_line_styles_category.SetValue(
            "Control Chart Center Line Dash"
        )
        self.combo_box_line_widths_category.SetValue(
            "Control Chart Center Line Width"
        )
        self.combo_box_sizes_category.SetValue("Plot Axis Label Font Size")

        self.checkbox_duplicates.SetValue(
            self.options.DUPLICATE_VALUE_DETECTION
        )
        self.combo_box_duplicates.Enable(
            self.options.DUPLICATE_VALUE_DETECTION
        )

        if is_windows():
            self.checkbox_edge_backend.SetValue(
                self.options.ENABLE_EDGE_BACKEND
            )
            self.checkbox_edge_backend.SetToolTip(
                "Allows for more complete plot interaction. Must restart "
                "IQDMA for change to be applied. If you cannot toggle this "
                "checkbox, Edge is not availabe. Requires MS Edge Beta to be "
                "installed: https://www.microsoftedgeinsider.com/en-us/download"
            )
        self.combo_box_pdf_ext.SetValue(
            "No" if self.options.PDF_IGNORE_EXT else "Yes"
        )
        self.combo_box_duplicates.SetValue(self.options.DUPLICATE_VALUE_POLICY)

    def __do_layout(self):
        sizer_wrapper = wx.BoxSizer(wx.VERTICAL)
        sizer_ok_cancel = wx.BoxSizer(wx.HORIZONTAL)
        sizer_plot_options = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Plot Options"), wx.VERTICAL
        )
        sizer_other_options = wx.StaticBoxSizer(
            wx.StaticBox(self, wx.ID_ANY, "Other Options"), wx.VERTICAL
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
        sizer_cc_limit = wx.BoxSizer(wx.HORIZONTAL)
        sizer_n_jobs = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pdf_ext = wx.BoxSizer(wx.HORIZONTAL)
        sizer_duplicate = wx.BoxSizer(wx.HORIZONTAL)

        label_colors = wx.StaticText(self, wx.ID_ANY, "Colors:")
        sizer_colors.Add(label_colors, 0, 0, 0)
        sizer_colors_input.Add(self.combo_box_colors_category, 0, 0, 0)
        sizer_colors_input.Add((20, 20), 0, 0, 0)
        sizer_colors_input.Add(self.combo_box_colors_selection, 0, 0, 0)
        sizer_colors.Add(sizer_colors_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_colors, 1, wx.EXPAND | wx.BOTTOM, 10)

        label_sizes = wx.StaticText(self, wx.ID_ANY, "Sizes:")
        sizer_sizes.Add(label_sizes, 0, 0, 0)
        sizer_sizes_input.Add(self.combo_box_sizes_category, 0, 0, 0)
        sizer_sizes_input.Add((20, 20), 0, 0, 0)
        sizer_sizes_input.Add(self.spin_ctrl_sizes_input, 0, 0, 0)
        sizer_sizes.Add(sizer_sizes_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_sizes, 1, wx.EXPAND | wx.BOTTOM, 10)

        label_line_widths = wx.StaticText(self, wx.ID_ANY, "Line Widths:")
        sizer_line_widths.Add(label_line_widths, 0, 0, 0)
        sizer_line_widths_input.Add(
            self.combo_box_line_widths_category, 0, 0, 0
        )
        sizer_line_widths_input.Add((20, 20), 0, 0, 0)
        sizer_line_widths_input.Add(self.spin_ctrl_line_widths_input, 0, 0, 0)
        sizer_line_widths.Add(sizer_line_widths_input, 1, wx.EXPAND, 0)
        sizer_plot_options.Add(sizer_line_widths, 1, wx.EXPAND | wx.BOTTOM, 10)

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
        sizer_plot_options.Add(sizer_line_styles, 1, wx.EXPAND | wx.BOTTOM, 10)

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

        label_cc_limit = wx.StaticText(
            self, wx.ID_ANY, "Control Limit (Std. Dev.):"
        )
        label_cc_limit.SetMinSize((175, 20))
        sizer_cc_limit.Add(label_cc_limit, 0, 0, 0)
        sizer_cc_limit.Add((20, 20), 0, 0, 0)
        sizer_cc_limit.Add(self.spin_ctrl_cc_std_dev, 0, 0, 0)
        sizer_other_options.Add(sizer_cc_limit, 0, wx.EXPAND | wx.BOTTOM, 10)

        label_duplicate = wx.StaticText(
            self, wx.ID_ANY, "Duplicate Value Policy:"
        )
        label_duplicate.SetMinSize((175, 20))
        sizer_duplicate.Add(label_duplicate, 0, 0, 0)
        sizer_duplicate.Add((20, 20), 0, 0, 0)
        sizer_duplicate.Add(self.combo_box_duplicates, 0, 0, 0)
        sizer_duplicate.Add((20, 20), 0, 0, 0)
        sizer_duplicate.Add(self.checkbox_duplicates, 0, 0, 0)
        sizer_other_options.Add(sizer_duplicate, 0, wx.EXPAND | wx.BOTTOM, 10)

        label_n_jobs = wx.StaticText(self, wx.ID_ANY, "Multi-Threading Jobs:")
        label_n_jobs.SetMinSize((175, 20))
        sizer_n_jobs.Add(label_n_jobs, 0, 0, 0)
        sizer_n_jobs.Add((20, 20), 0, 0, 0)
        sizer_n_jobs.Add(self.spin_ctrl_n_jobs, 0, 0, 0)
        sizer_other_options.Add(sizer_n_jobs, 0, wx.EXPAND | wx.BOTTOM, 10)

        label_ext = wx.StaticText(self, wx.ID_ANY, "Analyze .pdf only:")
        label_ext.SetMinSize((175, 20))
        sizer_pdf_ext.Add(label_ext, 0, 0, 0)
        sizer_pdf_ext.Add((20, 20), 0, 0, 0)
        sizer_pdf_ext.Add(self.combo_box_pdf_ext, 0, 0, 0)
        sizer_other_options.Add(sizer_pdf_ext, 0, wx.EXPAND, 0)
        sizer_wrapper.Add(
            sizer_other_options,
            0,
            wx.EXPAND | wx.ALL,
            10,
        )

        sizer_ok_cancel.Add(self.button_restore_defaults, 0, wx.RIGHT, 20)
        sizer_ok_cancel.Add(self.button_apply, 0, wx.LEFT | wx.RIGHT, 5)
        sizer_ok_cancel.Add(self.button_ok, 0, wx.LEFT | wx.RIGHT, 5)
        sizer_ok_cancel.Add(self.button_cancel, 0, wx.LEFT | wx.RIGHT, 5)
        sizer_wrapper.Add(sizer_ok_cancel, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(sizer_wrapper)
        self.Layout()
        self.Fit()
        self.SetMinSize(self.GetSize())

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
            self.update_cc_limit_val,
            id=self.spin_ctrl_cc_std_dev.GetId(),
        )

        self.Bind(
            wx.EVT_TEXT,
            self.update_n_jobs_val,
            id=self.spin_ctrl_n_jobs.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_pdf_ext_val,
            id=self.combo_box_pdf_ext.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_duplicate_val,
            id=self.combo_box_duplicates.GetId(),
        )

        self.Bind(
            wx.EVT_CHECKBOX,
            self.on_enable_duplicate_detection,
            id=self.checkbox_duplicates.GetId(),
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
        self.options.set_option("PDF_N_JOBS", val)

    def update_pdf_ext_var(self, *args):
        val = "No" if self.options.PDF_IGNORE_EXT else "Yes"
        self.combo_box_pdf_ext.SetValue(val)

    def update_pdf_ext_val(self, *args):
        new = self.combo_box_pdf_ext.GetValue()
        self.options.set_option("PDF_IGNORE_EXT", new == "No")

    def update_duplicate_var(self, *args):
        self.combo_box_duplicates.SetValue(self.options.DUPLICATE_VALUE_POLICY)

    def update_duplicate_val(self, *args):
        self.reimport_required = True
        new = self.combo_box_duplicates.GetValue()
        self.options.set_option("DUPLICATE_VALUE_POLICY", new)

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

    def update_cc_limit_var(self, *args):
        self.spin_ctrl_cc_std_dev.SetValue(
            str(self.options.CONTROL_LIMIT_STD_DEV)
        )

    def update_cc_limit_val(self, *args):
        new = self.spin_ctrl_cc_std_dev.GetValue()
        try:
            val = float(new)
        except ValueError:
            val = 1.0
        self.options.set_option("CONTROL_LIMIT_STD_DEV", val)

    def refresh_options(self):
        self.update_alpha_var()
        self.update_input_colors_var()
        self.update_line_style_var()
        self.update_line_width_var()
        self.update_size_var()
        self.update_n_jobs_var()
        self.update_cc_limit_var()
        self.update_pdf_ext_var()
        self.update_duplicate_var()

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

    def on_enable_duplicate_detection(self, *evt):
        state = self.checkbox_duplicates.GetValue()
        self.options.set_option("DUPLICATE_VALUE_DETECTION", state)
        self.combo_box_duplicates.Enable(state)
        self.reimport_required = True

    def on_apply(self, *evt):
        self.apply_and_redraw_plots()

        # Used to track edits since last options save
        self.is_edited = True

        # Used to track edits since redraw, set to True on options.set_option()
        self.options.is_edited = False

    def apply_and_redraw_plots(self):
        self.parent.apply_plot_options()
        if self.reimport_required:
            self.parent.reimport()
            self.reimport_required = False
        else:
            self.parent.redraw_plots()


class ParserSelect(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="Import CSV Data")
        set_icon(self)
        self.parent = parent
        self.place_holder = "--- Select One ---"

        create_default_parsers()
        self.parsers = import_csv_templates()

        self.__add_layout_object()
        self.__do_bind()
        self.__do_layout()
        self.__set_properties()

    def __add_layout_object(self):
        choices = [self.place_holder] + sorted(list(self.parsers))
        style = wx.CB_DROPDOWN | wx.CB_READONLY
        self.combo_box = wx.ComboBox(
            self, wx.ID_ANY, choices=choices, style=style
        )

        self.button = {
            "Import": wx.Button(self, wx.ID_OK, "Import"),
            "Cancel": wx.Button(self, wx.ID_CANCEL, "Cancel"),
        }

    def __do_bind(self):
        self.Bind(wx.EVT_COMBOBOX, self.on_select, id=self.combo_box.GetId())

    def __do_layout(self):
        sizer_wrapper = wx.BoxSizer(wx.VERTICAL)
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, "CSV Format:")

        sizer_main.Add(label, 0, wx.EXPAND | wx.LEFT | wx.TOP, 5)
        sizer_main.Add(self.combo_box, 1, wx.EXPAND | wx.ALL, 5)

        sizer_buttons.Add(self.button["Import"], 0, wx.EXPAND | wx.ALL, 5)
        sizer_buttons.Add(self.button["Cancel"], 0, wx.EXPAND | wx.ALL, 5)
        sizer_main.Add(sizer_buttons, 1, wx.EXPAND | wx.RIGHT, 10)

        sizer_wrapper.Add(sizer_main, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer_wrapper)
        self.Fit()
        self.Center()

    def __set_properties(self):
        parser_name = self.detect_parser_name
        if parser_name in self.parsers:
            self.combo_box.SetValue(parser_name)
        else:
            self.combo_box.SetValue(self.place_holder)
        self.on_select()

    @property
    def detect_parser_name(self):
        # TODO: implement a more robust format detection
        report_file_path = self.parent.text_ctrl["file"].GetValue()
        return basename(report_file_path).split("_")[0]

    def on_select(self, *evt):
        value = self.combo_box.GetValue()
        self.parent.parser = value if value != self.place_holder else None
        self.button["Import"].Enable(value != self.place_holder)
