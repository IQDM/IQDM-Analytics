#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# stats.py
"""Modified DVHA-Stats for IQDM-PDF output"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

from iqdma.importer import ReportImporter
import numpy as np
from iqdma.utilities_dvha_stats import import_data


class IQDMStats:
    """Modified DVHAStats class for IQDM-PDF output"""

    def __init__(
        self,
        report_file_path: str,
        charting_column: str,
        multi_val_policy: str,
        duplicate_detection: bool,
        parser: str,
    ):
        """Initialize ``IQDMStats``

        Parameters
        ----------
        report_file_path : str
            File path to CSV output from IQDM-PDF
        charting_column : str
            Column of y-axis data
        multi_val_policy : str
            Duplicate value policy from options
        duplicate_detection : bool
            If true, apply a multi_value policy from options
        parser : str
            CSV format

        """
        imported_data = ReportImporter(
            report_file_path, parser, duplicate_detection
        )
        self.multi_val_policy = multi_val_policy
        data = imported_data(charting_column, self.multi_val_policy)
        self.uid_columns = imported_data.uid_col
        self.uid_data = data["uids"]
        self.criteria_columns = imported_data.criteria_col

        self.data, self.var_names = import_data(data["data"])
        self.x_axis = data["x_axis"]

    def get_index_description(self) -> tuple:
        """Get a dict of data and columns for :class:`.DataTable`

        Returns
        -------
        dict
            Keys are column names with values being a list of values
        list
            Column names in order to be displayed
        """
        table = {key: [] for key in self.criteria_columns}
        table["Index"] = list(range(len(self.var_names)))
        table["Reports"] = []
        columns = ["Index", "Reports"] + self.criteria_columns
        for i, var_name in enumerate(self.var_names):
            counts = len(self.data[:, i][~np.isnan(self.data[:, i])])
            table["Reports"].append(counts)
            for j, criteria in enumerate(var_name.split(" && ")):
                table[self.criteria_columns[j]].append(criteria)
        table["Index"].append(i + 1)
        table["Reports"].append("All")
        for col in self.criteria_columns:
            table[col].append("N/A")
        return table, columns

    @property
    def variable_count(self):
        """Number of variables in data

        Returns
        ----------
        int
            Number of columns in data"""
        return self.data.shape[1]

    def get_index_by_var_name(self, var_name: str or int):
        """Get the variable index by var_name

        Parameters
        ----------
        var_name : int, str
            The name (str) or index (int) of the variable of interest

        Returns
        ----------
        int
            The column index for the given var_name
        """
        if var_name in self.var_names:
            index = self.var_names.index(var_name)
        elif isinstance(var_name, int) and var_name in range(
            self.variable_count
        ):
            return var_name
        else:
            msg = "%s is not a valid var_name\n%s" % (
                var_name,
                ",".join(self.var_names),
            )
            raise AttributeError(msg)
        return index

    def univariate_control_chart(
        self,
        var_name: str or int,
        std: float or int = 3,
        ucl_limit: float or int = None,
        lcl_limit: float or int = None,
        range: tuple or list or np.ndarray = None,
    ):
        """
        Calculate control limits for a standard univariate Control Chart

        Parameters
        ----------
        var_name : str, int
            The name (str) or index (int) of teh variable to plot
        std : int, float, optional
            Number of standard deviations used to calculate if a y-value is
            out-of-control
        ucl_limit : float, optional
            Limit the upper control limit to this value
        lcl_limit : float, optional
            Limit the lower control limit to this value
        range : tuple, list, ndarray
            2-item object containing start and end index of ``data``

        Returns
        ----------
        stats.ControlChart
            stats.ControlChart class object
        """
        kwargs = {
            "std": std,
            "ucl_limit": ucl_limit,
            "lcl_limit": lcl_limit,
            "range": range,
        }
        if var_name == "All":
            func = (
                "max"
                if self.multi_val_policy not in {"min", "mean", "max"}
                else self.multi_val_policy
            )
            data = getattr(np, f"nan{func}")(self.data, 1)
            return ControlChart(data, **kwargs)
        index = self.get_index_by_var_name(var_name)
        return ControlChart(self.data[:, index], **kwargs)

    def univariate_control_charts(self, **kwargs):
        """
        Calculate Control charts for all variables

        Parameters
        ----------
        kwargs : any
            See univariate_control_chart for keyword parameters

        Returns
        ----------
        dict
            ControlChart class objects stored in a dictionary with
            var_names and indices as keys (can use var_name or index)
        """
        data = {}
        for i, key in enumerate(self.var_names):
            data[key] = self.univariate_control_chart(key, **kwargs)
            data[i] = data[key]
        data["All"] = self.univariate_control_chart("All", **kwargs)
        data[i + 1] = data["All"]
        return data


class ControlChart:
    """Calculate control limits for a standard univariate Control Chart"

    Parameters
    ----------
    y : list, np.ndarray
        Input data (1-D)
    std : int, float, optional
        Number of standard deviations used to calculate if a y-value is
        out-of-control.
    ucl_limit : float, optional
        Limit the upper control limit to this value
    lcl_limit : float, optional
        Limit the lower control limit to this value
    range : tuple, list, ndarray
        2-item object containing start and end index of ``y``
    """

    def __init__(
        self,
        y,
        std=3,
        ucl_limit=None,
        lcl_limit=None,
        x=None,
        range=None,
    ):
        """Initialization of a ControlChart"""

        self.y = np.array(y) if isinstance(y, list) else y
        self.x = x if x else np.linspace(1, len(self.y), len(self.y))
        self.std = std
        self.ucl_limit = ucl_limit
        self.lcl_limit = lcl_limit
        self.range = range

        # since moving range is calculated based on 2 consecutive points
        self.scalar_d = 1.128

    def __str__(self):
        """String representation of ControlChartData object"""
        msg = [
            "center_line: %0.3f" % self.center_line,
            "control_limits: %0.3f, %0.3f" % self.control_limits,
            "out_of_control: %s" % self.out_of_control,
        ]
        return "\n".join(msg)

    def __repr__(self):
        """Return the string representation"""
        return str(self)

    @property
    def x_ranged(self) -> list:
        """Return ``x`` within ``range``

        Returns
        -------
        list
            ``x`` data from ``range[0]`` to ``range[1]``
        """
        return (
            self.x
            if self.range is None
            else self.x[self.range[0] - 1 : self.range[1]]
        )

    @property
    def y_ranged(self):
        """Return ``y`` within ``range``

        Returns
        -------
        list
            ``y`` data  from ``range[0]`` to ``range[1]``
        """
        return (
            self.y
            if self.range is None
            else self.y[self.range[0] - 1 : self.range[1]]
        )

    @property
    def center_line(self):
        """Center line of charting data (i.e., mean value)

        Returns
        ----------
        np.ndarray, np.nan
            Mean value of y with np.mean() or np.nan if y is empty
        """
        data = remove_nan(self.y_ranged)
        if len(data):
            return np.mean(data)
        return np.nan

    @property
    def avg_moving_range(self):
        """Avg moving range based on 2 consecutive points

        Returns
        ----------
        np.ndarray, np.nan
            Average moving range. Returns NaN if arr is empty.
        """
        return avg_moving_range(self.y_ranged, nan_policy="omit")

    @property
    def sigma(self):
        """UCL/LCL = center_line +/- sigma * std

        Returns
        ----------
        np.ndarray, np.nan
            sigma or np.nan if arr is empty
        """
        return self.avg_moving_range / self.scalar_d

    @property
    def control_limits(self):
        """Calculate the lower and upper control limits

        Returns
        ----------
        lcl : float
            Lower Control Limit (LCL)
        ucl : float
            Upper Control Limit (UCL)
        """
        cl = self.center_line
        sigma = self.sigma

        ucl = cl + self.std * sigma
        lcl = cl - self.std * sigma

        if self.ucl_limit is not None and ucl > self.ucl_limit:
            ucl = self.ucl_limit
        if self.lcl_limit is not None and lcl < self.lcl_limit:
            lcl = self.lcl_limit

        return lcl, ucl

    @property
    def out_of_control(self):
        """Get the indices of out-of-control observations

        Returns
        ----------
        np.ndarray
            An array of indices that are not between the lower and upper
            control limits
        """
        lcl, ucl = self.control_limits
        high = np.argwhere(self.y_ranged > ucl)
        low = np.argwhere(self.y_ranged < lcl)
        return np.unique(np.concatenate([high, low]))

    @property
    def out_of_control_high(self):
        """Get the indices of observations > ucl

        Returns
        ----------
        np.ndarray
            An array of indices that are greater than the upper control limit
        """
        _, ucl = self.control_limits
        return np.argwhere(self.y_ranged > ucl)

    @property
    def out_of_control_low(self):
        """Get the indices of observations < lcl

        Returns
        ----------
        np.ndarray
            An array of indices that are less than the lower control limit
        """
        lcl, _ = self.control_limits
        return np.argwhere(self.y_ranged < lcl)

    @property
    def chart_data(self):
        """JSON compatible dict for chart generation

        Returns
        ----------
        dict
            Data used for Histogram visuals. Keys include 'x', 'y',
            'out_of_control', 'center_line', 'lcl', 'ucl'
        """
        lcl, ucl = self.control_limits
        return {
            "x": self.x_ranged.tolist(),
            "y": self.y_ranged.tolist(),
            "out_of_control": self.out_of_control.tolist(),
            "center_line": float(self.center_line),
            "lcl": float(lcl),
            "ucl": float(ucl),
        }


def avg_moving_range(arr, nan_policy="omit"):
    """Calculate the average moving range (over 2-consecutive point1)

    Parameters
    ----------
    arr : array-like (1-D)
        Input array. Must be positive 1-dimensional.
    nan_policy : str, optional
        Value must be one of the following: {‘propagate’, ‘raise’, ‘omit’}
        Defines how to handle when input contains nan. The following options
        are available (default is ‘omit’):
        ‘propagate’: returns nan
        ‘raise’: throws an error
        ‘omit’: performs the calculations ignoring nan values

    Returns
    ----------
    np.ndarray, np.nan
        Average moving range. Returns NaN if arr is empty
    """

    arr = process_nan_policy(arr, nan_policy)
    if len(arr) == 0:
        return np.nan
    return np.mean(np.absolute(np.diff(arr)))


def remove_nan(arr):
    """Remove indices from 1-D array with values of np.nan

    Parameters
    ----------
    arr : np.ndarray (1-D)
        Input array. Must be positive 1-dimensional.

    Returns
    ----------
    np.ndarray
        arr with NaN values deleted

    """
    return arr[~np.isnan(arr)]


def process_nan_policy(arr, nan_policy):
    """Calculate the average moving range (over 2-consecutive point1)

    Parameters
    ----------
    arr : array-like (1-D)
        Input array. Must be positive 1-dimensional.
    nan_policy : str
        Value must be one of the following: {‘propagate’, ‘raise’, ‘omit’}
        Defines how to handle when input contains nan. The following options
        are available (default is ‘omit’):
        ‘propagate’: returns nan
        ‘raise’: throws an error
        ‘omit’: performs the calculations ignoring nan values

    Returns
    ----------
    np.ndarray, np.nan
        Input array evaluated per nan_policy
    """

    arr_no_nan = remove_nan(arr)
    if len(arr_no_nan) != len(arr):
        if nan_policy == "raise":
            msg = "NaN values are not supported for avg_moving_range"
            raise NotImplementedError(msg)
        if nan_policy == "propagate":
            return np.nan
        if nan_policy == "omit":
            return arr_no_nan
    return arr
