#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# exporter.py
"""
Export current chart to HTML, SVG, or PNG
"""
# Copyright (c) 2016-2019 Dan Cutright
# This file is part of IQDM Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

import wx
from functools import partial
from iqdma.options import MATPLOTLIB_COLORS
from iqdma.utilities import set_msw_background_color, set_icon


class ExportFigure(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(
            self, parent, style=wx.SYSTEM_MENU | wx.CLOSE_BOX | wx.CAPTION
        )

        self.parent = parent
        self.options = parent.options
        self.plots = {
            "Control Chart": parent.plot,
        }

        button_keys = {"Export": wx.ID_ANY, "Dismiss": wx.ID_CANCEL}
        self.button = {
            key: wx.Button(self, button_id, key)
            for key, button_id in button_keys.items()
        }

        self.__set_input_widgets()
        self.__set_properties()
        self.__do_bind()
        self.__do_layout()

        self.getter = {
            int: self.get_text_ctrl_int,
            float: self.get_text_ctrl_float,
            str: self.get_combo_box,
        }

        set_msw_background_color(self)
        set_icon(self)

    def __set_input_widgets(self):
        self.input = {key: [] for key in self.options.save_fig_param.keys()}
        self.label = {key: [] for key in self.options.save_fig_param.keys()}
        self.text_ctrl = {}
        self.combo_box = {}
        for obj_type, attr_dict in self.options.save_fig_param.items():
            for attr, value in attr_dict.items():
                self.label[obj_type].append(
                    wx.StaticText(
                        self, wx.ID_ANY, attr.replace("_", " ").title() + ":"
                    )
                )
                if type(value) is str:
                    color_options = ["none"] + MATPLOTLIB_COLORS
                    self.input[obj_type].append(
                        wx.ComboBox(
                            self,
                            wx.ID_ANY,
                            choices=color_options,
                            style=wx.CB_DROPDOWN | wx.TE_READONLY,
                        )
                    )
                    self.input[obj_type][-1].SetValue(value)
                    self.combo_box[obj_type + "_" + attr] = self.input[
                        obj_type
                    ][-1]
                else:
                    if "alpha" in attr:
                        self.input[obj_type].append(
                            wx.SpinCtrlDouble(
                                self,
                                wx.ID_ANY,
                                "0",
                                min=0,
                                max=1,
                                inc=0.1,
                                style=wx.SP_ARROW_KEYS,
                            )
                        )
                        self.input[obj_type][-1].SetIncrement(0.1)
                        self.input[obj_type][-1].SetValue(str(value))
                    elif "width" in attr and obj_type == "legend":
                        self.input[obj_type].append(
                            wx.SpinCtrl(
                                self,
                                wx.ID_ANY,
                                "0",
                                min=0,
                                max=20,
                                style=wx.SP_ARROW_KEYS,
                            )
                        )
                        self.input[obj_type][-1].SetValue(str(value))
                    else:
                        self.input[obj_type].append(
                            wx.TextCtrl(self, wx.ID_ANY, str(value))
                        )
                    self.text_ctrl[obj_type + "_" + attr] = self.input[
                        obj_type
                    ][-1]

        # self.label_plot = wx.StaticText(self, wx.ID_ANY, "Plot:")
        # self.combo_plot = wx.ComboBox(
        #     self, wx.ID_ANY, style=wx.CB_DROPDOWN | wx.TE_READONLY
        # )

        # self.include_range = wx.CheckBox(self, wx.ID_ANY, "Apply Range Edits")

    def __set_properties(self):
        self.SetTitle("Export Figure")

        # self.combo_plot.SetItems(sorted(list(self.plots)))
        # self.combo_plot.SetValue("Control Chart")

        # range_init = (
        #     self.options.apply_range_edits
        #     if hasattr(self.options, "apply_range_edits")
        #     else False
        # )
        # self.include_range.SetValue(range_init)
        # self.include_range.SetToolTip(
        #     "Check this to alter the ranges from the current view. Leave a range field blank "
        #     "to use the current view's value.\n"
        #     "NOTE: These range edits do not apply to Machine Learning plot saves."
        # )
        # self.on_checkbox()  # Disable Range input objects by default

    def __do_bind(self):
        self.Bind(
            wx.EVT_BUTTON, self.on_export, id=self.button["Export"].GetId()
        )
        self.Bind(wx.EVT_BUTTON, self.on_dismiss, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # self.Bind(
        #     wx.EVT_CHECKBOX, self.on_checkbox, id=self.include_range.GetId()
        # )

    def __do_layout(self):
        sizer_wrapper = wx.BoxSizer(wx.VERTICAL)
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_input = {
            key: wx.StaticBoxSizer(
                wx.StaticBox(self, wx.ID_ANY, key.capitalize()), wx.VERTICAL
            )
            for key in ["figure", "legend"]
        }
        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)

        # sizer_input["figure"].Add(self.include_range, 0, 0, 0)

        for obj_type in ["figure", "legend"]:
            for i, input_obj in enumerate(self.input[obj_type]):
                sizer_input[obj_type].Add(
                    self.label[obj_type][i],
                    0,
                    wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
                    3,
                )
                sizer_input[obj_type].Add(
                    input_obj, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 3
                )
            sizer_main.Add(sizer_input[obj_type], 0, wx.EXPAND | wx.ALL, 5)

        # sizer_main.Add(self.label_plot, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        # sizer_main.Add(self.combo_plot, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        sizer_buttons.Add(self.button["Dismiss"], 1, wx.EXPAND | wx.ALL, 5)
        sizer_buttons.Add(self.button["Export"], 1, wx.EXPAND | wx.ALL, 5)
        sizer_main.Add(sizer_buttons, 1, wx.EXPAND | wx.ALL, 5)

        sizer_wrapper.Add(sizer_main, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer_wrapper)
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.SetMaxSize(self.GetSize())
        self.Layout()

        self.options.apply_window_position(self, "export_figure")

    @property
    def plot(self):
        # return self.plots[self.combo_plot.GetValue()]
        return self.plots["Control Chart"]

    @property
    def save_plot_function(self):
        return partial(self.plot.save_figure, self.attr_dicts)

    def on_export(self, *evt):
        self.validate_input()
        # self.plot.save_figure_dlg(
        #     self,
        #     "Save %s Figure" % self.combo_plot.GetValue(),
        #     attr_dicts=self.attr_dicts,
        # )
        self.plot.save_figure_dlg(
            self,
            "Save Control Chart Figure",
            attr_dicts=self.attr_dicts,
        )

    def get_text_ctrl_float(self, key):
        value = self.text_ctrl[key].GetValue()
        try:
            return float(value)
        except ValueError:
            return None

    def get_text_ctrl_int(self, key):
        value = self.text_ctrl[key].GetValue()
        try:
            return int(float(value))
        except ValueError:
            return None

    def get_combo_box(self, key):
        return self.combo_box[key].GetValue()

    def get_attr_dict(self, obj_type, save_mode=False):
        return {
            key: self.getter[type(value)](obj_type + "_" + key)
            for key, value in self.options.save_fig_param[obj_type].items()
            if save_mode
            # or (
            #     "range" not in key
            #     or ("range" in key and self.include_range.GetValue())
            # )
        }

    @property
    def attr_dicts(self):
        return {key: self.get_attr_dict(key) for key in self.input.keys()}

    @property
    def save_attr_dicts(self):
        return {
            key: self.get_attr_dict(key, save_mode=True)
            for key in self.input.keys()
            if self.get_attr_dict(key, save_mode=True) is not None
        }

    def on_dismiss(self, *evt):
        wx.CallAfter(self.on_close)

    def on_close(self, *evt):
        self.validate_input()
        self.options.save_window_position(self, "export_figure")
        self.save_options()
        self.parent.export_figure = None
        self.Destroy()

    def save_options(self):
        self.options.save_fig_param = self.save_attr_dicts
        # self.options.apply_range_edits = self.include_range.GetValue()
        self.options.save()

    # def on_checkbox(self, *evt):
    #     for i, obj in enumerate(self.input["figure"]):
    #         if "Range" in self.label["figure"][i].GetLabel():
    #             self.label["figure"][i].Enable(self.include_range.GetValue())
    #             obj.Enable(self.include_range.GetValue())

    def validate_input(self):
        """If any TextCtrl is invalid, set to stored options"""
        for key, obj in self.text_ctrl.items():
            if obj.GetValue() == "":
                obj_type, attr = key[: key.find("_")], key[key.find("_") + 1 :]
                stored_value = self.options.save_fig_param[obj_type][attr]
                new_value = self.getter[type(stored_value)](key)
                if new_value is None:
                    obj.SetValue(str(stored_value))
