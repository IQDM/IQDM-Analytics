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
from dvhastats.utilities import widen_data, csv_to_dict
from IQDMPDF.parsers.sncpatient import SNCPatientReport2020, SNCPatientCustom
from IQDMPDF.parsers.delta4 import Delta4Report
from IQDMPDF.parsers.verisoft import VeriSoftReport

PARSERS = {'SNCPatient2020': SNCPatientReport2020,
           'SNCPatientCustom': SNCPatientCustom,
           'Delta4Report': Delta4Report,
           'VeriSoftReport': VeriSoftReport}


class ReportImporter:
    """Class to import IQDM-PDF CSV output"""
    def __init__(self, report_file_path: str, charting_column: str):
        """Initialize ``ReportImporter``

        Parameters
        ----------
        report_file_path : str
            File path to CSV output from IQDM-PDF
        charting_column : str
            Column of y-axis data

        """
        data_dict = csv_to_dict(report_file_path)

        self.parser = PARSERS[basename(report_file_path).split('_')[0]]()
        self.columns = self.parser.columns
        self.analysis_columns = self.parser.analysis_columns

        self.uid_col = [self.columns[i] for i in self.analysis_columns['uid']]
        self.crit_col = [self.columns[i] for i in self.analysis_columns['criteria']]

        self.criteria_options = {col: set(data_dict[col]) for col in self.crit_col}

        kwargs = {'uid_columns': self.uid_col,
                  'x_data_cols': self.crit_col,
                  'y_data_col': charting_column,
                  'date_col':  self.columns[self.analysis_columns['date']],
                  'dtype': float}
        self.data = widen_data(data_dict, **kwargs)
        self.x_axis = self.data.pop('date')
        self.uids = self.data.pop('uid')
