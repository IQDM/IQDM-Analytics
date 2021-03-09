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
from iqdma.utilities_dvha_stats import widen_data, csv_to_dict
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
        return [self.columns[i] for i in self.analysis_columns["uid"]]

    @property
    def criteria_col(self) -> list:
        return [self.columns[i] for i in self.analysis_columns["criteria"]]

    @property
    def charting_options(self):
        return [self.columns[y["index"]] for y in self.analysis_columns["y"]]

    @property
    def ucl(self):
        y_names = self.charting_options
        return {
            y_names[i]: y["ucl_limit"]
            for i, y in enumerate(self.analysis_columns["y"])
        }

    @property
    def lcl(self):
        y_names = self.charting_options
        return {
            y_names[i]: y["lcl_limit"]
            for i, y in enumerate(self.analysis_columns["y"])
        }

    @property
    def criteria_options(self) -> dict:
        ans = {}
        for col in self.criteria_col:
            clean_options = []
            for option in set(self.data_dict[col]):
                try:
                    clean_options.append(str(float(option)))
                except ValueError:
                    clean_options.append(option)
            ans[col] = sorted(list(set(clean_options)))

        return ans

    def delta4_dtype_func(self, val):
        val = val.strip()
        if "%" in val:
            return float(val.split("%")[0].strip())
        elif " " in val:
            return float(val.split(" ")[0].strip())
        return float(val)

    def __call__(self, charting_column: str) -> dict:
        """

        Parameters
        ----------
        charting_column : str
            Column of y-axis data

        Returns
        -------
        dict

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
        }
        data = widen_data(self.data_dict, **kwargs)
        x_axis = data.pop("date")
        uids = data.pop("uid")

        return {"data": data, "x_axis": x_axis, "uids": uids}
