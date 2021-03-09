#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# main.py
"""main file for IQDM Analytics"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

import wx
from numpy import isnan
import webbrowser
from os.path import isfile
from iqdma.stats import IQDMStats
from iqdma.plot import PlotControlChart
from iqdma.options import Options, DefaultOptions
from iqdma.dialogs import UserSettings, About
from iqdma.paths import ICONS
from iqdma.data_table import DataTable
from iqdma.importer import ReportImporter
from iqdma.exporter import ExportFigure
from iqdma.pdf_miner import ProgressFrame
from iqdma.utilities import (
    is_windows,
    is_mac,
    is_linux,
    scale_bitmap,
    set_frame_icon,
    ErrorDialog,
)


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        # Prevent resize event triggers during app launch
        self.allow_window_size_save = False

        self.range_update_needed = True

        self.user_settings = None
        self.export_figure = None
        self.pdf_miner_window = None
        self.importer = None
        self.report_data = None
        self.control_chart_data = None
        self.options = Options()
        self.set_to_hist = False
        # self.is_plot_initialized = False

        self.panel = wx.Panel(self, wx.ID_ANY)
        self.plot = PlotControlChart(self.panel, self.options)

        self.__add_menubar()
        self.__add_tool_bar()
        self.__add_layout_objects()
        self.__do_bind()
        self.__set_tooltips()
        self.__set_properties()
        self.__do_layout()

        self.options.apply_window_position(self, "main")
        self.allow_window_size_save = True

    def __set_properties(self):
        self.SetTitle("IQDM Analytics")
        self.frame_toolbar.Realize()

    def __add_tool_bar(self):
        self.toolbar_keys = [
            "Open",
            "Save",
            "PDF Miner",
            "Settings",
        ]
        self.toolbar_ids = {
            key: i + 1000 for i, key in enumerate(self.toolbar_keys)
        }

        self.frame_toolbar = wx.ToolBar(
            self, -1, style=wx.TB_HORIZONTAL | wx.TB_TEXT
        )
        self.SetToolBar(self.frame_toolbar)

        description = {
            "PDF Miner": "Parse IMRT QA Reports into CSV",
            "Open": "Load a CSV file from IQDM PDF Miner",
            "Save": "Save Current Chart",
            "Settings": "User Settings",
        }
        for key in self.toolbar_keys:
            bitmap = wx.Bitmap(ICONS[key], wx.BITMAP_TYPE_ANY)
            if is_windows() or is_linux():
                bitmap = scale_bitmap(bitmap, 30, 30)
            self.frame_toolbar.AddTool(
                self.toolbar_ids[key],
                key,
                bitmap,
                wx.NullBitmap,
                wx.ITEM_NORMAL,
                description[key],
                "",
            )

        self.Bind(
            wx.EVT_TOOL, self.on_pdf_miner, id=self.toolbar_ids["PDF Miner"]
        )
        self.Bind(wx.EVT_TOOL, self.on_browse, id=self.toolbar_ids["Open"])
        self.Bind(wx.EVT_TOOL, self.on_save, id=self.toolbar_ids["Save"])
        self.Bind(
            wx.EVT_TOOL,
            self.on_pref,
            id=self.toolbar_ids["Settings"],
        )

    def __add_menubar(self):

        self.frame_menubar = wx.MenuBar()

        file_menu = wx.Menu()
        menu_open = file_menu.Append(wx.ID_ANY, "&Open\tCtrl+O")
        menu_save = file_menu.Append(wx.ID_ANY, "&Save\tCtrl+S")
        qmi = file_menu.Append(wx.ID_ANY, "&Quit\tCtrl+Q")

        settings_menu = wx.Menu()
        menu_pref = settings_menu.Append(wx.ID_PREFERENCES)

        help_menu = wx.Menu()
        menu_github = help_menu.Append(wx.ID_ANY, "GitHub Page")
        menu_report_issue = help_menu.Append(wx.ID_ANY, "Report an Issue")
        menu_about = help_menu.Append(wx.ID_ANY, "&About")

        # self.Bind(wx.EVT_MENU, self.on_pref, menu_settings)
        self.Bind(wx.EVT_MENU, self.on_quit, qmi)
        self.Bind(wx.EVT_MENU, self.on_browse, menu_open)
        self.Bind(wx.EVT_MENU, self.on_save, menu_save)
        self.Bind(wx.EVT_MENU, self.on_pref, menu_pref)
        if is_mac():
            menu_user_settings = settings_menu.Append(
                wx.ID_ANY, "&Preferences\tCtrl+,"
            )
            self.Bind(wx.EVT_MENU, self.on_pref, menu_user_settings)

        menu_win_pos = settings_menu.Append(wx.ID_ANY, "Reset Windows")

        self.Bind(wx.EVT_MENU, self.on_reset_windows, menu_win_pos)
        self.Bind(wx.EVT_MENU, self.on_githubpage, menu_github)
        self.Bind(wx.EVT_MENU, self.on_report_issue, menu_report_issue)
        self.Bind(wx.EVT_MENU, About, menu_about)

        self.frame_menubar.Append(file_menu, "&File")
        self.frame_menubar.Append(settings_menu, "&Settings")
        self.frame_menubar.Append(help_menu, "&Help")
        self.SetMenuBar(self.frame_menubar)

    def __add_layout_objects(self):
        self.text_ctrl = {"file": wx.TextCtrl(self.panel, wx.ID_ANY, "")}
        self.button = {
            "browse": wx.Button(self.panel, wx.ID_ANY, "Browse…"),
            "refresh": wx.Button(self.panel, wx.ID_REFRESH),
        }
        self.button["refresh"].Disable()

        self.check_box = {
            "hippa": wx.CheckBox(self.panel, wx.ID_ANY, "HIPPA Mode")
        }
        self.combo_box = {
            "y": wx.ComboBox(
                self.panel, wx.ID_ANY, style=wx.CB_DROPDOWN | wx.CB_READONLY
            )
        }
        self.spin_ctrl = {
            "bins": wx.SpinCtrl(
                self.panel,
                wx.ID_ANY,
                "10",
                min=2,
                max=100,
                style=wx.SP_ARROW_KEYS,
            ),
            "start": wx.SpinCtrl(
                self.panel,
                wx.ID_ANY,
                "1",
                min=1,
                max=100,
                style=wx.SP_ARROW_KEYS | wx.TE_PROCESS_ENTER,
            ),
            "stop": wx.SpinCtrl(
                self.panel,
                wx.ID_ANY,
                "1",
                min=1,
                max=100,
                style=wx.SP_ARROW_KEYS,
            ),
        }
        if is_mac():
            for key in self.spin_ctrl.keys():
                self.text_ctrl[key] = self.spin_ctrl[key].GetChildren()[0]
                self.text_ctrl[key].SetWindowStyle(
                    self.text_ctrl[key].GetWindowStyle() | wx.TE_PROCESS_ENTER
                )

        style = (
            wx.BORDER_SUNKEN
            | wx.LC_HRULES
            | wx.LC_REPORT
            | wx.LC_VRULES
            | wx.LC_SINGLE_SEL
        )
        self.list_ctrl_table = wx.ListCtrl(self.panel, wx.ID_ANY, style=style)
        self.data_table = DataTable(self.list_ctrl_table)

        self.sizer = {}

        static_box_sizers = {
            "main": ("Charts", wx.VERTICAL),
            "file": ("File Selection", wx.HORIZONTAL),
            "criteria": ("Pass-Rate Criteria", wx.VERTICAL),
        }
        for key, box in static_box_sizers.items():
            self.sizer[key] = wx.StaticBoxSizer(
                wx.StaticBox(self.panel, wx.ID_ANY, box[0]), box[1]
            )
        self.sizer["y"] = wx.BoxSizer(wx.HORIZONTAL)

    def __do_bind(self):
        self.Bind(
            wx.EVT_BUTTON, self.on_browse, id=self.button["browse"].GetId()
        )
        self.Bind(wx.EVT_BUTTON, self.on_refresh, id=wx.ID_REFRESH)
        self.Bind(
            wx.EVT_TEXT, self.enable_refresh, id=self.text_ctrl["file"].GetId()
        )
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_CLOSE, self.on_quit)
        self.Bind(
            wx.EVT_LIST_COL_CLICK,
            self.sort_table,
            self.list_ctrl_table,
        )
        self.Bind(
            wx.EVT_LIST_ITEM_SELECTED,
            self.on_table_select,
            self.list_ctrl_table,
        )
        self.Bind(
            wx.EVT_CHAR_HOOK,
            self.data_table.increment_index,
            id=self.list_ctrl_table.GetId(),
        )
        self.Bind(
            wx.EVT_COMBOBOX,
            self.update_report_data,
            id=self.combo_box["y"].GetId(),
        )
        self.Bind(
            wx.EVT_CHECKBOX,
            self.update_report_data,
            id=self.check_box["hippa"].GetId(),
        )
        self.Bind(
            wx.EVT_SPINCTRL,
            self.on_range_spin,
            id=self.spin_ctrl["start"].GetId(),
        )
        self.Bind(
            wx.EVT_SPINCTRL,
            self.on_range_spin,
            id=self.spin_ctrl["stop"].GetId(),
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_range_spin,
            id=self.spin_ctrl["start"].GetId(),
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.on_range_spin,
            id=self.spin_ctrl["stop"].GetId(),
        )
        self.Bind(
            wx.EVT_SPINCTRL,
            self.update_report_data_from_hist,
            id=self.spin_ctrl["bins"].GetId(),
        )
        self.Bind(
            wx.EVT_TEXT_ENTER,
            self.update_report_data_from_hist,
            id=self.spin_ctrl["bins"].GetId(),
        )
        # self.Bind(wx.EVT_SPIN, self.update_report_data_from_hist,
        #           id=self.spin_ctrl['bins'].GetId())

    def __set_tooltips(self):
        self.check_box["hippa"].SetToolTip(
            "Hide date and ID from chart hover tooltips."
        )

    def __do_layout(self):
        wrapper = wx.BoxSizer(wx.VERTICAL)

        # File objects
        self.sizer["file"].Add(
            self.text_ctrl["file"], 1, wx.EXPAND | wx.ALL, 5
        )
        self.sizer["file"].Add(self.button["refresh"], 0, wx.ALL, 5)
        self.sizer["file"].Add(self.button["browse"], 0, wx.ALL, 5)

        # Analysis Criteria Objects
        self.sizer["criteria"].Add(
            self.list_ctrl_table, 0, wx.EXPAND | wx.ALL, 5
        )

        self.sizer["y"].Add(self.check_box["hippa"], 1, wx.EXPAND | wx.LEFT, 5)
        label_start = wx.StaticText(self.panel, wx.ID_ANY, "Start:")
        self.sizer["y"].Add(label_start, 0, wx.EXPAND | wx.RIGHT, 5)
        self.sizer["y"].Add(
            self.spin_ctrl["start"], 0, wx.EXPAND | wx.RIGHT, 10
        )
        label_end = wx.StaticText(self.panel, wx.ID_ANY, "Stop:")
        self.sizer["y"].Add(label_end, 0, wx.EXPAND | wx.RIGHT, 5)
        self.sizer["y"].Add(
            self.spin_ctrl["stop"], 0, wx.EXPAND | wx.RIGHT, 10
        )
        label_bins = wx.StaticText(self.panel, wx.ID_ANY, "Hist. Bins:")
        self.sizer["y"].Add(label_bins, 0, wx.EXPAND| wx.RIGHT, 5)
        self.sizer["y"].Add(
            self.spin_ctrl["bins"], 0, wx.EXPAND | wx.RIGHT, 10
        )
        label = wx.StaticText(self.panel, wx.ID_ANY, "Charting Variable:")
        self.sizer["y"].Add(label, 0, wx.EXPAND | wx.RIGHT, 5)
        self.sizer["y"].Add(self.combo_box["y"], 0, wx.RIGHT, 5)
        self.sizer["main"].Add(self.sizer["y"], 0, wx.EXPAND, 0)

        self.plot.init_layout()
        self.sizer["main"].Add(self.plot.layout, 1, wx.EXPAND | wx.ALL, 5)

        wrapper.Add(self.sizer["file"], 0, wx.ALL | wx.EXPAND, 5)
        wrapper.Add(self.sizer["criteria"], 0, wx.ALL | wx.EXPAND, 5)
        wrapper.Add(self.sizer["main"], 1, wx.EXPAND | wx.ALL, 5)

        if is_windows():
            self.spin_ctrl['start'].SetMinSize((80, self.spin_ctrl['start'].GetSize()[1]))
            self.spin_ctrl['stop'].SetMinSize(
                (80, self.spin_ctrl['stop'].GetSize()[1]))
            self.spin_ctrl['bins'].SetMinSize(
                (70, self.spin_ctrl['bins'].GetSize()[1]))

        self.panel.SetSizer(wrapper)
        self.SetMinSize(self.options.MIN_RESOLUTION_MAIN)
        self.panel.Fit()
        self.Fit()
        self.Layout()
        self.Center()

    def __apply_size_and_position(self):
        self.Fit()
        self.Center()
        self.options.apply_window_position(self, "main")
        self.allow_window_size_save = True

    def on_resize(self, *evt):
        try:
            if self.allow_window_size_save:
                self.options.set_window_size(self, "main")
            self.Refresh()
            self.Layout()
            wx.CallAfter(self.plot.redraw_plot)
        except RuntimeError:
            pass

    def on_move(self, *evt):
        try:
            if self.allow_window_size_save:
                self.options.save_window_position(self, "main")
        except Exception:
            pass

    def on_reset_windows(self, *evt):
        defaults = DefaultOptions()
        for key in ["MIN_RESOLUTION_MAIN", "MAX_INIT_RESOLUTION_MAIN"]:
            self.options.set_option(key, getattr(defaults, key))
        self.options.clear_positions()
        self.options.clear_window_sizes()
        self.__apply_size_and_position()

    def on_quit(self, *evt):
        self.options.save()
        self.close_windows()
        self.Destroy()

    def close_windows(self):
        if self.user_settings is not None:
            self.user_settings.Close()

        if self.export_figure is not None:
            self.export_figure.Close()

        if self.pdf_miner_window is not None:
            try:
                self.pdf_miner_window.close()
            except RuntimeError:
                pass

    def on_save(self, evt):
        if not self.report_data:
            msg = "Please load data from CSV first."
            caption = "No Chart to Save!"
            ErrorDialog(self, msg, caption)
            return

        if self.export_figure is None:
            try:
                self.export_figure = ExportFigure(self)
            except Exception:
                self.options.save_fig_param = DefaultOptions().save_fig_param
                self.export_figure = ExportFigure(self)
            self.export_figure.Show()
        else:
            self.export_figure.Raise()

    def on_pref(self, *args):
        if self.user_settings is None:
            self.user_settings = UserSettings(self)
            self.user_settings.Show()
        else:
            self.user_settings.Raise()

    def on_pdf_miner(self, *evt):
        if self.pdf_miner_window is None:
            self.pdf_miner_window = ProgressFrame(self.options)
        else:
            self.pdf_miner_window.Raise()

    @staticmethod
    def on_githubpage(*evt):
        webbrowser.open_new_tab("https://github.com/IQDM/IQDM-Analytics")

    @staticmethod
    def on_report_issue(*evt):
        webbrowser.open_new_tab(
            "https://github.com/IQDM/IQDM-Analytics/issues"
        )

    def on_browse(self, *evt):
        dlg = wx.FileDialog(
            self,
            "Load IQDM-PDF CSV",
            "",
            wildcard="*.csv",
            style=wx.FD_FILE_MUST_EXIST | wx.FD_OPEN,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.text_ctrl["file"].SetValue(dlg.GetPath())
            self.import_csv()

        dlg.Destroy()

    def on_refresh(self, *evt):
        self.import_csv()

    def enable_refresh(self, *evt):
        self.button["refresh"].Enable(
            isfile(self.text_ctrl["file"].GetValue())
        )

    ################################################################
    # Data Processing and Visualization
    ################################################################
    def import_csv(self):
        # if not self.is_plot_initialized:
        #     self.plot.init_layout()
        #     self.sizer["main"].Add(self.plot.layout, 1, wx.EXPAND | wx.ALL, 5)
        #     self.panel.Layout()
        #     self.is_plot_initialized = True
        self.plot.clear_plot()
        self.importer = ReportImporter(self.text_ctrl["file"].GetValue())
        options = self.importer.charting_options
        self.combo_box["y"].Clear()
        self.combo_box["y"].Append(options)
        self.combo_box["y"].SetValue(options[0])
        self.range_update_needed = True
        self.update_report_data()

    def update_report_data(self, *evt):

        index = 0
        if len(self.data_table.selected_row_index):
            table_index = self.data_table.selected_row_index[0]
            index = self.data_table.get_value(table_index, 0)

        self.report_data = IQDMStats(
            self.text_ctrl["file"].GetValue(), self.charting_variable
        )
        table, columns = self.report_data.get_index_description()
        self.data_table.set_data(table, columns)
        self.data_table.set_column_widths(auto=True)

        if self.range_update_needed:
            self.update_range_spinners()

        self.update_control_chart_data()

        if len(table[columns[0]]):
            if index > self.data_table.row_count:
                index = 0
            self.list_ctrl_table.Select(index)
            self.range_update_needed = False

    def update_range_spinners(self):
        if self.report_data and self.report_data.x_axis:
            max_length = len(self.report_data.x_axis)
        else:
            max_length = 0

        self.spin_ctrl["stop"].SetMax(max_length)
        self.spin_ctrl["start"].SetValue(1)
        self.spin_ctrl["stop"].SetValue(max_length)

        self.spin_ctrl["start"].SetMax(self.spin_ctrl["stop"].GetValue())
        self.spin_ctrl["stop"].SetMin(self.spin_ctrl["start"].GetValue())

    @property
    def range(self):
        return [self.spin_ctrl[key].GetValue() for key in ["start", "stop"]]

    def update_control_chart_data(self):
        self.control_chart_data = self.report_data.univariate_control_charts(
            ucl_limit=self.ucl, lcl_limit=self.lcl, range=self.range
        )
        self.on_table_select()

    def on_range_spin(self, *evt):
        self.update_control_chart_data()

    def update_report_data_from_hist(self, *evt):
        self.set_to_hist = True
        self.update_control_chart_data()

    @property
    def charting_variable(self):
        return self.combo_box["y"].GetValue()

    @property
    def ucl(self):
        return self.importer.ucl[self.charting_variable]

    @property
    def lcl(self):
        return self.importer.lcl[self.charting_variable]

    def on_table_select(self, *evt):
        selected = self.data_table.selected_row_index
        if selected:
            index = self.data_table.get_value(selected[0], 0)
            self.update_chart_data(index)
            self.list_ctrl_table.SetFocus()
        else:
            self.plot.clear_plot()

    def update_chart_data(self, index):
        ucc = self.control_chart_data[index]
        data = ucc.chart_data
        lcl, ucl = ucc.control_limits
        lcl = ucc.center_line if isnan(lcl) else lcl
        ucl = ucc.center_line if isnan(ucl) else ucl
        if self.check_box["hippa"].GetValue():
            dates = data_id = ["Redacted"] * len(self.report_data.uid_data)
        else:
            data_id = [
                f"{v.split(' && ')[0]} - {v.split(' && ')[1]}"
                for v in self.report_data.uid_data
            ]
            dates = self.report_data.x_axis
        start, stop = tuple(self.range)
        kwargs = {
            "x": data["x"],
            "y": data["y"],
            "data_id": data_id[start - 1 : stop],
            "dates": dates[start - 1 : stop],
            "center_line": ucc.center_line,
            "ucl": ucl,
            "lcl": lcl,
            "y_axis_label": self.combo_box["y"].GetValue(),
            "bins": int(self.spin_ctrl["bins"].GetValue()),
            "tab": 1 if self.set_to_hist else 0,
        }
        self.plot.update_plot(**kwargs)
        self.set_to_hist = False

    def sort_table(self, evt):
        self.data_table.sort_table(evt)
        self.data_table.set_column_widths(auto=True)

    def apply_plot_options(self):
        self.plot.apply_options()

    def redraw_plots(self):
        self.on_table_select(None)


class MainApp(wx.App):
    def OnInit(self):
        if is_windows():
            from iqdma.windows_reg_edit import (
                set_ie_emulation_level,
                set_ie_lockdown_level,
            )

            set_ie_emulation_level()
            set_ie_lockdown_level()
        self.SetAppName("IQDM Analytics")
        self.frame = MainFrame(None, wx.ID_ANY, "")
        set_frame_icon(self.frame)
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


def start():
    app = MainApp(0)
    app.MainLoop()
