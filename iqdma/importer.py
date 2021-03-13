#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# importer.py
"""Import output from IQDM-PDF"""
#
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

from os.path import basename
from iqdma.utilities import widen_data
from iqdma.utilities_dvha_stats import csv_to_dict
from IQDMPDF.parsers.sncpatient import SNCPatientReport2020, SNCPatientCustom
from IQDMPDF.parsers.delta4 import Delta4Report
from IQDMPDF.parsers.verisoft import VeriSoftReport

PARSERS = {
    "SNCPatient2020": SNCPatientReport2020,
    "SNCPatientCustom": SNCPatientCustom,
    "Delta4": Delta4Report,
    "VeriSoft": VeriSoftReport,
}


class ReportImporter:
    """Class to import IQDM-PDF CSV output"""

    def __init__(self, report_file_path: str):
        """Initialize ``ReportImporter``

        Parameters
        ----------
        report_file_path : str
            File path to CSV output from IQDM-PDF

        """
        self.data_dict = csv_to_dict(report_file_path)

        self.parser = PARSERS[basename(report_file_path).split("_")[0]]()
        self.columns = self.parser.columns
        self.analysis_columns = self.parser.analysis_columns

    @property
    def uid_col(self) -> list:
        """Column names, when combined create a UID

        Returns
        -------
        list
            Column names from ``analysis_columns['uid']``
        """
        return [self.columns[i] for i in self.analysis_columns["uid"]]

    @property
    def criteria_col(self) -> list:
        """Column names of analysis criteria options

        Returns
        -------
        list
            Column names from ``analysis_columns['criteria']``
        """
        return [self.columns[i] for i in self.analysis_columns["criteria"]]

    @property
    def charting_options(self) -> list:
        """Column names of y-axis options

        Returns
        -------
        list
            Column names from ``analysis_columns['y']``
        """
        return [self.columns[y["index"]] for y in self.analysis_columns["y"]]

    @property
    def ucl(self) -> dict:
        """Upper Control Limit caps

        Returns
        -------
        dict
            keys are column names, values are maximum UCL values (or None)
        """
        y_names = self.charting_options
        return {
            y_names[i]: y["ucl_limit"]
            for i, y in enumerate(self.analysis_columns["y"])
        }

    @property
    def lcl(self):
        """Lower Control Limit minimums

        Returns
        -------
        dict
            keys are column names, values are minimum LCL values (or None)
        """
        y_names = self.charting_options
        return {
            y_names[i]: y["lcl_limit"]
            for i, y in enumerate(self.analysis_columns["y"])
        }

    @staticmethod
    def delta4_dtype_func(val: str) -> float:
        """Process Delta4 report values, use to highjack ``dtype`` in
        ``widen_data``

        Parameters
        ----------
        val : str
            Value from Delta4 IQDM-PDF CSV output

        Returns
        -------
        float
            ``val`` converted into a float
        """
        val = val.strip()
        try:
            if "%" in val:
                return float(val.split("%")[0].strip())
            elif " " in val:
                return float(val.split(" ")[0].strip())
            return float(val)
        except ValueError:
            return float("nan")

    def __call__(
        self, charting_column: str, multi_val_policy: str = "first"
    ) -> dict:
        """Call ``widen`` data with ``data_dict`` and ``charting_column``

        Parameters
        ----------
        charting_column : str
            Column of y-axis data

        Returns
        -------
        dict of list
            Keys of 'data', 'x_axis', and 'uids'

        """

        dtype = (
            self.delta4_dtype_func
            if isinstance(self.parser, Delta4Report)
            else float
        )

        kwargs = {
            "uid_columns": self.uid_col,
            "x_data_cols": self.criteria_col,
            "y_data_col": charting_column,
            "date_col": self.columns[self.analysis_columns["date"]],
            "dtype": dtype,
            "date_col_file_creation": "report_file_creation",
            "multi_val_policy": multi_val_policy,
        }
        data = widen_data(self.data_dict, **kwargs)
        x_axis = data.pop("date")
        uids = data.pop("uid")

        return {"data": data, "x_axis": x_axis, "uids": uids}
