#!/usr/bin/env python
# -*- coding: utf-8 -*-

# models.plot.py
"""
Classes to generate bokeh plots
"""
# Copyright (c) 2016-2019 Dan Cutright
# This file is part of DVH Analytics, released under a BSD license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/cutright/DVH-Analytics

import wx.html2
from functools import partial
from bokeh.plotting import figure
from bokeh.io.export import get_layout_html, export_svgs, export_png
from bokeh.models import Legend, HoverTool, ColumnDataSource, Div, Spacer
from bokeh.models.widgets import Panel, Tabs
from bokeh.layouts import column, row
from os.path import join, isdir, splitext
from os import makedirs, unlink
from iqdma.utilities import (
    is_windows,
    save_data_to_file,
    FIG_WILDCARDS,
    ErrorDialog,
    get_windows_webview_backend,
)
from iqdma.paths import TEMP_DIR, APP_DIR
from iqdma.options import Options
import numpy as np


DEFAULT_TOOLS = "pan,box_zoom,crosshair,reset"

enable_edge = Options().ENABLE_EDGE_BACKEND
BACKEND = get_windows_webview_backend(enable_edge)


class Plot:
    """
    Base class for all other plots
    Pass the layout property into a wx sizer
    """

    def __init__(
        self,
        parent,
        options,
        x_axis_label="X Axis",
        y_axis_label="Y Axis",
        x_axis_type="linear",
        tools=DEFAULT_TOOLS,
        apply_grid_options=True,
    ):
        """
        :param parent: the wx UI object where the plot will be displayed
        :param options: user options object for visual preferences
        :type options: Options
        :param x_axis_label: text for the x-axis title
        :type x_axis_label: str
        :param y_axis_label: text for the y-axis title
        :type y_axis_label: str
        :param x_axis_type: x axis type per bokeh (e.g., 'linear' or 'datetime')
        :type x_axis_type: str
        """

        self.options = options
        self.parent = parent
        self.size_factor = (0.95, 0.95)
        self.size_offset = (0, 100) if is_windows() else (50, 400)
        self.layout = None
        self.bokeh_layout = None
        self.html_str = ""

        # For windows users, since wx.html2 requires a file to load rather
        # than passing a string. The file name for each plot will be
        # join(TEMP_DIR, "%s.html" % self.type)
        self.type = None

        self.figure = figure(
            x_axis_type=x_axis_type,
            tools=tools,
            toolbar_sticky=True,
            active_drag="box_zoom",
        )
        self.figures = [self.figure]  # keep track of all figures
        self.figure.toolbar.logo = None
        self.set_figure_dimensions()
        self.figure.xaxis.axis_label = x_axis_label
        self.figure.yaxis.axis_label = y_axis_label

        self.figures_attr = (
            []
        )  # temporary storage of figure dimensions/colors during export
        self.legends = []
        self.legends_attr = (
            []
        )  # temporary storage of legend dimensions/colors during export
        self.figures_attr_include_sub_keys = True
        self.apply_grid_options = apply_grid_options

        self.source = {}  # Will be a dictionary of bokeh ColumnDataSources

        if self.options:
            self.__apply_default_figure_options()

    def __apply_default_figure_options(self):
        self.figure.xaxis.axis_label_text_font_size = (
            self.options.PLOT_AXIS_LABEL_FONT_SIZE
        )
        self.figure.yaxis.axis_label_text_font_size = (
            self.options.PLOT_AXIS_LABEL_FONT_SIZE
        )
        self.figure.xaxis.major_label_text_font_size = (
            self.options.PLOT_AXIS_MAJOR_LABEL_FONT_SIZE
        )
        self.figure.yaxis.major_label_text_font_size = (
            self.options.PLOT_AXIS_MAJOR_LABEL_FONT_SIZE
        )
        self.figure.min_border = self.options.MIN_BORDER
        self.figure.yaxis.axis_label_text_baseline = "bottom"

        if self.apply_grid_options:
            for fig in self.figures:
                fig.grid.grid_line_alpha = self.options.GRID_ALPHA
                fig.grid.grid_line_width = self.options.GRID_LINE_WIDTH
                fig.grid.grid_line_color = self.options.GRID_LINE_COLOR

    def add_legend(self, fig, legend_items=None):
        if legend_items is None:
            legend_items = self.legend_items
        legend = Legend(items=legend_items, orientation="horizontal")
        self.legends.append(legend)

        # Add the layout outside the plot, clicking legend item hides the line
        fig.add_layout(legend, "above")
        fig.legend.click_policy = "hide"

    @property
    def legend_items(self):
        # must be over-ridden
        return []

    def clear_plot(self):
        if self.bokeh_layout:
            self.clear_sources()
            self.figure.xaxis.axis_label = ""
            self.figure.yaxis.axis_label = ""
            self.update_bokeh_layout_in_wx_python()

    def clear_source(self, source_key):
        data = {
            data_key: [] for data_key in list(self.source[source_key].data)
        }
        self.source[source_key].data = data

    def clear_sources(self):
        for key in list(self.source):
            self.clear_source(key)

    def set_layout(self):
        if BACKEND is None:
            self.layout = wx.html2.WebView.New(self.parent)
        else:
            self.layout = wx.html2.WebView.New(
                self.parent, backend=BACKEND["id"]
            )

    def init_layout(self):
        self.set_layout()
        self.update_bokeh_layout_in_wx_python()

    def update_bokeh_layout_in_wx_python(self):
        if self.layout is not None:
            self.html_str = get_layout_html(self.bokeh_layout)
            if is_windows():  # Windows requires LoadURL()
                if not isdir(TEMP_DIR):
                    makedirs(TEMP_DIR)
                web_file = join(TEMP_DIR, "%s.html" % self.type)
                try:
                    unlink(web_file)
                except Exception:
                    pass
                with open(web_file, "wb") as f:
                    f.write(self.html_str.encode("utf-8"))
                self.layout.LoadURL(web_file)
            else:
                self.layout.SetPage(self.html_str, "")

    def set_obj_attr(self, obj_attr_dict, obj_type="figure"):
        """During plot export, user can supply custom figure properties,
        apply these and store original values"""
        if obj_type == "legend":
            self.legends_attr = []
            obj_attr = self.legends_attr
            objects = self.legends
        else:
            self.figures_attr = []
            obj_attr = self.figures_attr
            objects = self.figures

        for obj in objects:
            top_keys = [
                key
                for key in obj_attr_dict.keys()
                if (not key.endswith("_start") and not key.endswith("_end"))
            ]
            sub_keys = set(obj_attr_dict.keys()) - set(top_keys)
            current_attr = {key: getattr(obj, key) for key in top_keys}
            if self.figures_attr_include_sub_keys:
                for key in sub_keys:
                    top_key = key[: key.rfind("_")]
                    sub_key = key[key.rfind("_") + 1 :]
                    current_attr[key] = getattr(getattr(obj, top_key), sub_key)

            obj_attr.append(current_attr)
            for key, value in obj_attr_dict.items():
                if value is not None:
                    value = None if value == "none" else value
                    if key in top_keys:
                        setattr(obj, key, value)
                    elif self.figures_attr_include_sub_keys:
                        top_key = key[: key.rfind("_")]
                        sub_key = key[key.rfind("_") + 1 :]
                        setattr(getattr(obj, top_key), sub_key, value)

    def load_stored_obj_attr(self, obj_type="figure"):
        """Restore the figure properties before set_fig_attr was called"""

        stored_attr = (
            self.legends_attr if obj_type == "legend" else self.figures_attr
        )
        objects = self.figures if obj_type == "figure" else self.legends

        for i, obj in enumerate(objects):
            for key, value in stored_attr[i].items():
                if key.endswith("_start") or key.endswith("_end"):
                    top_key = key[: key.rfind("_")]
                    sub_key = key[key.rfind("_") + 1 :]
                    setattr(getattr(obj, top_key), sub_key, value)
                else:
                    setattr(obj, key, value)

    def set_obj_attrs(self, attr_dicts):
        if attr_dicts:
            for key, attr_dict in attr_dicts.items():
                self.set_obj_attr(attr_dicts[key], obj_type=key)

    def load_obj_attrs(self, attr_dicts):
        if attr_dicts:
            for key in attr_dicts.keys():
                self.load_stored_obj_attr(obj_type=key)

    def save_figure(self, attr_dicts, file_name):
        figure_format = splitext(file_name)[1][1:].lower()
        self.set_obj_attrs(attr_dicts)
        getattr(self, "export_%s" % figure_format)(file_name)
        self.load_obj_attrs(attr_dicts)

    def export_svg(self, file_name):
        for f, fig in enumerate(self.figures):
            if self.figure_has_data(fig):
                fig.output_backend = "svg"
                if len(self.figures) > 1:
                    f_split = splitext(file_name)
                    f_name = f"{f_split[0]}_{f+1}{f_split[1]}"
                else:
                    f_name = file_name
                export_svgs(fig, filename=f_name, timeout=10)
                fig.output_backend = "canvas"

    @staticmethod
    def figure_has_data(fig):
        if fig.renderers:
            data = fig.renderers[0].data_source.data
            if data and len(list(data)) and len(data[list(data)[0]]):
                return True
        return False

    def export_png(self, file_name):
        export_png(self.bokeh_layout, filename=file_name, timeout=10)

    def export_html(self, file_name):
        with open(file_name, "w", encoding="utf-8") as doc:
            doc.write(get_layout_html(self.bokeh_layout))

    @staticmethod
    def clean_data(*data, data_id=None, uid=None, dates=None):
        """
        Data used for statistical analysis in Regression and Control Charts
        requires no 'None' values and the same number of points for each
        variable.  To mitigate this, clean_data will find all studies that
        have any 'None' values and return data without these studies
        :param data: any number of variables, each being a list of values
        :param data_id: data_ids in same order as data
        :param uid: study instance uids in same order data
        :param dates: sim study dates in same order as data
        :return: data only including studies with no 'None' values
        :rtype: tuple
        """
        bad_indices = []
        for var in data:
            bad_indices.extend(
                [i for i, value in enumerate(var) if value == "None"]
            )
        bad_indices = set(bad_indices)

        ans = [
            [value for i, value in enumerate(var) if i not in bad_indices]
            for var in data
        ]

        for var in [data_id, uid, dates]:
            if var is not None:
                ans.append(
                    [
                        value
                        for i, value in enumerate(var)
                        if i not in bad_indices
                    ]
                )

        return tuple(ans)

    def set_figure_dimensions(self):
        size = [
            int(d * self.size_factor[i] - self.size_offset[i])
            for i, d in enumerate(self.parent.GetSize())
        ]
        for fig in self.figures:
            fig.plot_width = max(size[0], 100)
            fig.plot_height = max(size[1], 100)

    def redraw_plot(self):
        if self.layout is not None:
            self.set_figure_dimensions()
            self.update_bokeh_layout_in_wx_python()

    def apply_options(self):
        self.__apply_default_figure_options()

    def save_figure_dlg(self, parent, title, attr_dicts=None):
        try:
            file_name = save_data_to_file(
                parent,
                title,
                partial(self.save_figure, attr_dicts),
                data_type="function",
                wildcard=FIG_WILDCARDS,
            )
            if file_name is not None:
                ErrorDialog(
                    parent,
                    "Output saved to %s" % file_name,
                    "Save Successful",
                    flags=wx.OK | wx.OK_DEFAULT,
                )
        except Exception as e:
            if "phantomjs is not present" in str(e).lower():
                msg = (
                    "Please download a phantomjs executable from "
                    "https://phantomjs.org/download.html and store in "
                    f"{APP_DIR} or try a phantomjs installation "
                    "with conda or npm"
                )
            else:
                msg = str(e)
            ErrorDialog(parent, msg, "Save Error")


class PlotControlChart(Plot):
    """
    Generate plot for Control Chart frame
    """

    def __init__(self, parent, options):
        """
        :param parent: the wx UI object where the plot will be displayed
        :param options: user preferences
        :type options: Options
        """
        Plot.__init__(self, parent, options, x_axis_label="Study")

        self.type = "control_chart"

        self.y_axis_label = ""
        self.options = options
        self.source = {
            "plot": ColumnDataSource(
                data=dict(x=[], y=[], data_id=[], color=[], alpha=[], dates=[])
            ),
            "hist": ColumnDataSource(
                data=dict(x=[], top=[], width=[], range=[])
            ),
            "center_line": ColumnDataSource(data=dict(x=[], y=[], data_id=[])),
            "ucl_line": ColumnDataSource(data=dict(x=[], y=[], data_id=[])),
            "lcl_line": ColumnDataSource(data=dict(x=[], y=[], data_id=[])),
            "bound": ColumnDataSource(
                data=dict(x=[], data_id=[], upper=[], avg=[], lower=[])
            ),
            "patch": ColumnDataSource(data=dict(x=[], y=[])),
        }

        self.__add_plot_data()
        self.__add_histogram_data()
        self.__add_hover()
        self.__create_divs()
        self.add_legend(self.figure)
        self.__do_layout()

        self.apply_options()

    def __add_plot_data(self):
        self.plot_data = self.figure.circle(
            "x", "y", source=self.source["plot"], alpha="alpha", color="color"
        )
        self.plot_data_line = self.figure.line(
            "x",
            "y",
            source=self.source["plot"],
        )
        self.plot_patch = self.figure.patch(
            "x", "y", source=self.source["patch"]
        )

        self.plot_center_line = self.figure.line(
            "x", "y", source=self.source["center_line"]
        )
        self.plot_lcl_line = self.figure.line(
            "x", "y", source=self.source["lcl_line"]
        )
        self.plot_ucl_line = self.figure.line(
            "x", "y", source=self.source["ucl_line"]
        )

    def __add_histogram_data(self):
        self.histogram = figure(tools="")
        self.figures.append(self.histogram)
        self.vbar = self.histogram.vbar(
            x="x",
            width="width",
            bottom=0,
            top="top",
            source=self.source["hist"],
        )

        self.histogram.xaxis.axis_label = ""
        self.histogram.yaxis.axis_label = "Frequency"

    def __add_hover(self):
        self.figure.add_tools(
            HoverTool(
                show_arrow=True,
                tooltips=[
                    ("Study", "@x"),
                    ("Date", "@dates"),
                    ("ID", "@data_id"),
                    ("Value", "@y{0.2f}"),
                ],
                renderers=[self.plot_data],
            )
        )

        self.histogram.add_tools(
            HoverTool(
                show_arrow=True,
                line_policy="next",
                mode="vline",
                tooltips=[
                    ("Bin Center", "@x{0.2f}"),
                    ("Bin Range", "@range"),
                    ("Counts", "@top"),
                ],
                renderers=[self.vbar],
            )
        )

    @property
    def legend_items(self):
        return [
            ("Charting Variable   ", [self.plot_data]),
            ("Charting Variable Line  ", [self.plot_data_line]),
            ("Center Line   ", [self.plot_center_line]),
            ("UCL  ", [self.plot_ucl_line]),
            ("LCL  ", [self.plot_lcl_line]),
        ]

    def __create_divs(self):
        self.div_total = Div(text="", width=80)
        self.div_std = Div(text="", width=80)
        self.div_ic = Div(text="", width=65)
        self.div_ooc = Div(text="", width=80)
        self.div_center_line = Div(text="", width=150)
        self.div_ucl = Div(text="", width=120)
        self.div_lcl = Div(text="", width=120)

    def __do_layout(self):

        control_chart = column(
            self.figure,
            row(
                self.div_total,
                self.div_std,
                self.div_ic,
                self.div_ooc,
                self.div_center_line,
                self.div_ucl,
                self.div_lcl,
            ),
        )
        histogram = column(Spacer(height=30), self.histogram)
        tab1 = Panel(child=control_chart, title="Control Chart")
        tab2 = Panel(child=histogram, title="Histogram")

        self.bokeh_layout = Tabs(tabs=[tab1, tab2])

    def update_plot(
        self,
        x,
        y,
        data_id,
        dates,
        center_line,
        ucl,
        lcl,
        std=None,
        y_axis_label="Y Axis",
        update_layout=True,
        cl_overrides=None,
        bins=10,
        tab=0,
    ):
        self.bokeh_layout.active = tab
        self.set_figure_dimensions()
        self.clear_sources()
        self.y_axis_label = y_axis_label
        self.figure.xaxis.axis_label = "Study"
        self.figure.yaxis.axis_label = self.y_axis_label
        if len(x) > 1:

            if cl_overrides is not None:
                if "UCL" in cl_overrides and cl_overrides["UCL"] is not None:
                    ucl = cl_overrides["UCL"]
                if "LCL" in cl_overrides and cl_overrides["LCL"] is not None:
                    lcl = cl_overrides["LCL"]

            plot_color = self.options.PLOT_COLOR
            ooc_color = self.options.CONTROL_CHART_OUT_OF_CONTROL_COLOR

            colors = [ooc_color, plot_color]
            alphas = [
                self.options.CONTROL_CHART_OUT_OF_CONTROL_ALPHA,
                self.options.CONTROL_CHART_CIRCLE_ALPHA,
            ]
            color = [colors[ucl >= value >= lcl] for value in y]
            alpha = [alphas[ucl >= value >= lcl] for value in y]
            ic = [
                c == plot_color
                for i, c in enumerate(color)
                if not np.isnan(y[i])
            ]

            self.source["plot"].data = {
                "x": x,
                "y": y,
                "data_id": data_id,
                "color": color,
                "alpha": alpha,
                "dates": dates,
            }

            self.source["patch"].data = {
                "x": [x[0], x[-1], x[-1], x[0]],
                "y": [ucl, ucl, lcl, lcl],
                "color": [plot_color] * 4,
            }
            self.source["center_line"].data = {
                "x": [min(x), max(x)],
                "y": [center_line] * 2,
                "data_id": ["center line"] * 2,
            }

            self.source["lcl_line"].data = {
                "x": [min(x), max(x)],
                "y": [lcl] * 2,
                "data_id": ["center line"] * 2,
            }
            self.source["ucl_line"].data = {
                "x": [min(x), max(x)],
                "y": [ucl] * 2,
                "data_id": ["center line"] * 2,
            }

            self.div_total.text = "<b>Total</b>: %d" % np.count_nonzero(
                ~np.isnan(y)
            )
            self.div_center_line.text = (
                "<b>Center line</b>: %0.3f" % center_line
            )
            self.div_std.text = "<b>sigma</b>: %s" % std
            self.div_ucl.text = "<b>UCL</b>: %0.3f" % ucl
            self.div_lcl.text = "<b>LCL</b>: %0.3f" % lcl
            self.div_ic.text = "<b>IC</b>: %d" % ic.count(True)
            self.div_ooc.text = "<b>OOC</b>: %d" % ic.count(False)

            self.update_histogram(bins)

        else:
            self.clear_sources()
            self.clear_plot()

        if update_layout:
            self.update_bokeh_layout_in_wx_python()

    def update_histogram(self, bin_size=10):
        self.histogram.xaxis.axis_label = self.figure.yaxis.axis_label
        width_fraction = 0.9
        self.source["hist"].data = {
            "x": [],
            "top": [],
            "width": [],
        }

        if self.source["plot"].data["y"]:
            try:
                y = [
                    v for v in self.source["plot"].data["y"] if not np.isnan(v)
                ]
                hist, bins = np.histogram(y, bins=bin_size)
                width = [width_fraction * (bins[1] - bins[0])] * bin_size
                center = (bins[:-1] + bins[1:]) / 2.0
                range_ = [
                    "%0.2f - %0.2f" % (bins[i], bins[i + 1])
                    for i in range(len(bins) - 1)
                ]
                self.source["hist"].data = {
                    "x": center,
                    "top": hist,
                    "width": width,
                    "range": range_,
                }
            except Exception as e:
                print(e)

    def apply_options(self):
        super().apply_options()

        for circle_plot in ["plot_data"]:
            glyph = getattr(self, circle_plot).glyph
            glyph.size = getattr(
                self.options, "CONTROL_CHART_%s" % "CIRCLE_SIZE"
            )

        glyph = self.plot_data_line.glyph
        glyph.line_color = getattr(self.options, "CONTROL_CHART_LINE_COLOR")
        glyph.line_width = getattr(self.options, "CONTROL_CHART_LINE_WIDTH")
        glyph.line_dash = getattr(self.options, "CONTROL_CHART_LINE_DASH")
        glyph.line_alpha = getattr(self.options, "CONTROL_CHART_CIRCLE_ALPHA")

        for line_plot in ["data", "center_line", "lcl_line", "ucl_line"]:
            glyph = getattr(self, "plot_%s" % (line_plot)).glyph
            modifier = (
                "LINE_" if line_plot == "data" else "%s_" % line_plot.upper()
            )
            glyph.line_color = getattr(
                self.options, "CONTROL_CHART_%s%s" % (modifier, "COLOR")
            )
            glyph.line_width = getattr(
                self.options, "CONTROL_CHART_%s%s" % (modifier, "WIDTH")
            )
            glyph.line_dash = getattr(
                self.options, "CONTROL_CHART_%s%s" % (modifier, "DASH")
            )
            if line_plot != "data":
                glyph.line_alpha = getattr(
                    self.options,
                    "CONTROL_CHART_%s%s" % (modifier, "ALPHA"),
                )

            # patches
            glyph = getattr(self, "plot_patch").glyph
            glyph.fill_color = getattr(
                self.options, "CONTROL_CHART_PATCH_COLOR"
            )
            glyph.fill_alpha = getattr(
                self.options, "CONTROL_CHART_PATCH_ALPHA"
            )
            glyph.line_color = getattr(
                self.options, "CONTROL_CHART_PATCH_COLOR"
            )
            glyph.line_alpha = getattr(
                self.options, "CONTROL_CHART_PATCH_ALPHA"
            )

        self.histogram.xaxis.axis_label_text_font_size = (
            self.options.PLOT_AXIS_LABEL_FONT_SIZE
        )
        self.histogram.yaxis.axis_label_text_font_size = (
            self.options.PLOT_AXIS_LABEL_FONT_SIZE
        )
        self.histogram.xaxis.major_label_text_font_size = (
            self.options.PLOT_AXIS_MAJOR_LABEL_FONT_SIZE
        )
        self.histogram.yaxis.major_label_text_font_size = (
            self.options.PLOT_AXIS_MAJOR_LABEL_FONT_SIZE
        )
        self.histogram.min_border_left = self.options.MIN_BORDER
        self.histogram.min_border_bottom = self.options.MIN_BORDER

        glyph = self.vbar.glyph
        glyph.line_color = self.options.PLOT_COLOR
        glyph.fill_color = self.options.PLOT_COLOR
        glyph.line_alpha = self.options.HISTOGRAM_ALPHA
        glyph.fill_alpha = self.options.HISTOGRAM_ALPHA
