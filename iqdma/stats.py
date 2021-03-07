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
from dvhastats.ui import DVHAStats
import numpy as np


class IQDMStats(DVHAStats):
    """Modified DVHAStats class for IQDM-PDF output"""

    def __init__(self, report_file_path: str, charting_column: str):
        """Initialize ``IQDMStats``

        Parameters
        ----------
        report_file_path : str
            File path to CSV output from IQDM-PDF
        charting_column : str
            Column of y-axis data

        """
        imported_data = ReportImporter(report_file_path)
        data = imported_data(charting_column)
        self.uid_columns = imported_data.uid_col
        self.uid_data = data["uids"]
        self.criteria_columns = imported_data.criteria_col
        self.criteria_options = imported_data.criteria_options
        super().__init__(data["data"], x_axis=data["x_axis"])

    def print_data_index_by_criteria(self):
        for i, var_name in enumerate(self.var_names):
            print(f"index: {i}")
            for j, criteria in enumerate(var_name.split(" && ")):
                print(f"\t{self.criteria_columns[j]}: {criteria}")
            print("\n")

    def get_index_description(self):
        table = {key: [] for key in self.criteria_columns}
        table["Index"] = list(range(len(self.var_names)))
        table["Reports"] = []
        columns = ["Index", "Reports"] + self.criteria_columns
        for i, var_name in enumerate(self.var_names):
            counts = len(self.data[:, i][~np.isnan(self.data[:, i])])
            table["Reports"].append(counts)
            for j, criteria in enumerate(var_name.split(" && ")):
                table[self.criteria_columns[j]].append(criteria)
        return table, columns
