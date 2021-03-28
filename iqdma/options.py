#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# options.py
"""options file for IQDM Analytics"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

import pickle
from os.path import isfile
from os import unlink
import hashlib
from iqdma.paths import OPTIONS_PATH, OPTIONS_CHECKSUM_PATH
from iqdma._version import __version__
from iqdma.utilities import push_to_log


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

        # Adjust the opacity of the histograms
        self.HISTOGRAM_ALPHA = 0.5

        self.save_fig_param = {
            "figure": {
                # "y_range_start": -0.0005,
                # "x_range_start": 0.0,
                # "y_range_end": 1.0005,
                # "x_range_end": 10000.0,
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

        self.CONTROL_LIMIT_STD_DEV = 3

        self.DUPLICATE_VALUE_POLICY = "last"
        self.DUPLICATE_VALUE_OPTIONS = ["first", "last", "max", "mean", "min"]
        self.DUPLICATE_VALUE_DETECTION = True


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
                msg = (
                    "Options.load: Options file corrupted. Loading "
                    "default options."
                )
                push_to_log(e, msg=msg)
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
            msg = "Options.set_option: %s did not previously exist" % attr
            push_to_log(msg)

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
            msg = (
                "Options.is_options_file_valid: Corrupted options file "
                "detected. Loading default options."
            )
            push_to_log(e, msg=msg)
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


MATPLOTLIB_COLORS = [
    "aliceblue",
    "antiquewhite",
    "aqua",
    "aquamarine",
    "azure",
    "beige",
    "bisque",
    "black",
    "blanchedalmond",
    "blue",
    "blueviolet",
    "brown",
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "cornsilk",
    "crimson",
    "cyan",
    "darkblue",
    "darkcyan",
    "darkgoldenrod",
    "darkgray",
    "darkgreen",
    "darkgrey",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "deeppink",
    "deepskyblue",
    "dimgray",
    "dimgrey",
    "dodgerblue",
    "firebrick",
    "floralwhite",
    "forestgreen",
    "fuchsia",
    "gainsboro",
    "ghostwhite",
    "gold",
    "goldenrod",
    "gray",
    "green",
    "greenyellow",
    "grey",
    "honeydew",
    "hotpink",
    "indianred",
    "indigo",
    "ivory",
    "khaki",
    "lavender",
    "lavenderblush",
    "lawngreen",
    "lemonchiffon",
    "lightblue",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgray",
    "lightgreen",
    "lightgrey",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "lime",
    "limegreen",
    "linen",
    "magenta",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "navy",
    "oldlace",
    "olive",
    "olivedrab",
    "orange",
    "orangered",
    "orchid",
    "palegoldenrod",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "purple",
    "rebeccapurple",
    "red",
    "rosybrown",
    "royalblue",
    "saddlebrown",
    "salmon",
    "sandybrown",
    "seagreen",
    "seashell",
    "sienna",
    "silver",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "springgreen",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "turquoise",
    "violet",
    "wheat",
    "white",
    "whitesmoke",
    "yellow",
    "yellowgreen",
]
