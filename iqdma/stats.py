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
        imported_data = ReportImporter(report_file_path, charting_column)
        self.criteria_columns = imported_data.crit_col
        self.criteria_options = imported_data.criteria_options
        super().__init__(imported_data.data, x_axis=imported_data.x_axis)

    def print_data_index_by_criteria(self):
        for i, var_name in enumerate(self.var_names):
            print(f"index: {i}")
            for j, criteria in enumerate(var_name.split(' && ')):
                print(f"\t{self.criteria_columns[j]}: {criteria}")
            print('\n')
