#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# main.py
"""main file for IQDM Analytics GUI"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics
import wx
from iqdma.stats import IQDMStats
from iqdma.plot import PlotControlChart
from iqdma.options import Options, DefaultOptions, UserSettings
from iqdma.utilities import (
    is_windows,
    is_mac,
    is_linux,
    scale_bitmap,
    set_frame_icon,
)
from iqdma.paths import ICONS, LICENSE_PATH
from iqdma.data_table import DataTable
from iqdma.importer import ReportImporter
from iqdma.exporter import ExportFigure
from iqdma.pdf_miner import ProgressFrame
from numpy import isnan
import webbrowser


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.allow_window_size_save = False

        self.user_settings = None
        self.export_figure = None

        self.options = Options()

        self.panel = wx.Panel(self, wx.ID_ANY)
        self.plot = PlotControlChart(self.panel, self.options)

        self.importer = None
        self.report_data = None
        self.control_chart_data = None

        self.__add_menubar()
        self.__add_tool_bar()
        self.__add_layout_objects()
        self.__do_bind()
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
        self.button = {"browse": wx.Button(self.panel, wx.ID_ANY, "Browse")}

        self.combo_box = {"y": wx.ComboBox(self.panel, wx.ID_ANY, style=wx.CB_DROPDOWN | wx.CB_READONLY)}

        style = (
            wx.BORDER_SUNKEN
            | wx.LC_HRULES
            | wx.LC_REPORT
            | wx.LC_VRULES
            | wx.LC_SINGLE_SEL
        )
        self.list_ctrl_table = wx.ListCtrl(self.panel, wx.ID_ANY, style=style)
        self.data_table = DataTable(self.list_ctrl_table)

    def __do_bind(self):
        self.Bind(
            wx.EVT_BUTTON, self.on_browse, id=self.button["browse"].GetId()
        )
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_MOVE, self.on_move)
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
        self.Bind(wx.EVT_CHAR_HOOK, self.data_table.increment_index)
        self.Bind(wx.EVT_COMBOBOX, self.update_report_data, id=self.combo_box["y"].GetId())

    def __do_layout(self):
        sizer = {}
        wrapper = wx.BoxSizer(wx.VERTICAL)

        static_box_sizers = {
            "main": ("Control Chart", wx.VERTICAL),
            "file": ("File Selection", wx.HORIZONTAL),
            "criteria": ("Pass-Rate Criteria", wx.VERTICAL),
        }
        for key, box in static_box_sizers.items():
            sizer[key] = wx.StaticBoxSizer(
                wx.StaticBox(self.panel, wx.ID_ANY, box[0]), box[1]
            )
        sizer["y"] = wx.BoxSizer(wx.HORIZONTAL)

        # File objects
        sizer["file"].Add(self.text_ctrl["file"], 1, wx.EXPAND | wx.ALL, 5)
        sizer["file"].Add(self.button["browse"], 0, wx.ALL, 5)

        # Analysis Criteria Objects
        sizer["criteria"].Add(self.list_ctrl_table, 0, wx.EXPAND | wx.ALL, 10)

        sizer["y"].Add((20, 20), 1, wx.EXPAND, 0)
        label = wx.StaticText(self.panel, wx.ID_ANY, "Charting Variable:")
        sizer["y"].Add(label, 0, wx.EXPAND, 0)
        sizer["y"].Add(self.combo_box["y"], 0, 0, 0)
        sizer["main"].Add(sizer["y"], 0, wx.EXPAND, 0)
        self.plot.init_layout()
        sizer["main"].Add(self.plot.layout, 1, wx.EXPAND | wx.ALL, 5)

        wrapper.Add(sizer["file"], 0, wx.ALL | wx.EXPAND, 10)
        wrapper.Add(sizer["criteria"], 0, wx.ALL | wx.EXPAND, 10)
        wrapper.Add(sizer["main"], 1, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(wrapper)
        self.SetMinSize(self.options.MIN_RESOLUTION_MAIN)
        self.panel.Fit()
        self.Fit()
        self.Layout()
        self.Center()

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

    def import_csv(self):
        self.plot.clear_plot()
        self.importer = ReportImporter(self.text_ctrl["file"].GetValue())
        options = self.importer.charting_options
        self.combo_box['y'].Clear()
        self.combo_box['y'].Append(options)
        self.combo_box['y'].SetValue(options[0])
        self.update_report_data()

    def update_report_data(self, *evt):

        index = 0
        if len(self.data_table.selected_row_index):
            index = self.data_table.selected_row_index[0]

        self.report_data = IQDMStats(
            self.text_ctrl["file"].GetValue(), self.charting_variable
        )
        table, columns = self.report_data.get_index_description()
        self.data_table.set_data(table, columns)
        self.data_table.set_column_widths(auto=True)
        self.control_chart_data = self.report_data.univariate_control_charts(ucl_limit=self.ucl, lcl_limit=self.lcl)
        if len(table[columns[0]]):
            self.list_ctrl_table.Select(index)

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
            self.update_chart_data(selected[0])
        else:
            self.plot.clear_plot()

    def update_chart_data(self, index):
        ucc = self.control_chart_data[index]
        data = ucc.chart_data
        lcl, ucl = ucc.control_limits
        lcl = ucc.center_line if isnan(lcl) else lcl
        ucl = ucc.center_line if isnan(ucl) else ucl
        data_id = [
            f"{v.split(' && ')[0]} - {v.split(' && ')[1]}"
            for v in self.report_data.uid_data
        ]
        kwargs = {
            "x": data["x"],
            "y": data["y"],
            "data_id": data_id,
            "dates": self.report_data.x_axis,
            "center_line": ucc.center_line,
            "ucl": ucl,
            "lcl": lcl,
            "y_axis_label": self.combo_box['y'].GetValue(),
        }
        self.plot.update_plot(**kwargs)

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

    def __apply_size_and_position(self):
        self.Fit()
        self.Center()
        self.options.apply_window_position(self, "main")
        self.allow_window_size_save = True

    def on_quit(self, *evt):
        self.close_windows()
        self.Destroy()

    def close_windows(self):
        if self.user_settings is not None:
            self.user_settings.Close()

        if self.export_figure is not None:
            self.export_figure.Close()

    def on_save(self, evt):
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

    def sort_table(self, evt):
        self.data_table.sort_table(evt)
        self.data_table.set_column_widths(auto=True)

    def apply_plot_options(self):
        self.plot.apply_options()

    def redraw_plots(self):
        self.on_table_select(None)

    @staticmethod
    def on_githubpage(*evt):
        webbrowser.open_new_tab("https://github.com/IQDM/IQDM-Analytics")

    @staticmethod
    def on_report_issue(*evt):
        webbrowser.open_new_tab(
            "https://github.com/IQDM/IQDM-Analytics/issues"
        )

    def on_pdf_miner(self, *evt):
        dlg = wx.DirDialog(
            self,
            "Parse IMRT QA Reports",
            "",
            style=wx.DD_DIR_MUST_EXIST | wx.DD_DEFAULT_STYLE,
        )

        init_dir = None
        if dlg.ShowModal() == wx.ID_OK:
            init_dir = dlg.GetPath()
        dlg.Destroy()

        if init_dir:
            dlg = wx.DirDialog(
                self,
                "Select Output Directory for IMRT QA Reports",
                "",
                style=wx.DD_DIR_MUST_EXIST | wx.DD_DEFAULT_STYLE,
            )

            output_dir = None
            if dlg.ShowModal() == wx.ID_OK:
                output_dir = dlg.GetPath()
            dlg.Destroy()
            if output_dir:
                kwargs = {'init_directory': init_dir,
                          'output_dir': output_dir,
                          'ignore_extension': self.options.PDF_IGNORE_EXT,
                          'processes': self.options.PDF_N_JOBS}
                ProgressFrame(kwargs)


class About(wx.Dialog):
    """
    Simple dialog to display the LICENSE file and a brief text header in a scrollable window
    """

    def __init__(self, *evt):
        wx.Dialog.__init__(self, None, title="About IQDM Analytics")

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

    def OnExit(self):
        self.frame.options.save()
        for window in wx.GetTopLevelWindows():
            wx.CallAfter(window.Close)
        return super().OnExit()


def start():
    app = MainApp(0)
    app.MainLoop()
