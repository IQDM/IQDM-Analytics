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

from shutil import copyfile
from iqdma.utilities import widen_data, push_to_log
from iqdma.utilities_dvha_stats import csv_to_dict
from IQDMPDF.parsers.sncpatient import SNCPatientReport2020, SNCPatientCustom
from IQDMPDF.parsers.delta4 import Delta4Report
from IQDMPDF.parsers.verisoft import VeriSoftReport
from IQDMPDF.parsers.generic import ParserBase
import json
from os.path import basename, isdir, join, splitext, isfile
from os import listdir
from iqdma.paths import CSV_TEMPLATES_DIR, DEFAULT_CSV_TEMPLATES_DIR
import re


DEFAULT_PARSERS = {
    "SNCPatient2020": SNCPatientReport2020,
    "SNCPatientCustom": SNCPatientCustom,
    "Delta4": Delta4Report,
    "VeriSoft": VeriSoftReport,
}


class CSVParser:
    """Import CSV Template from JSON"""

    def __init__(self, json_file_path: str):
        """Initialization of CSVParser

        Parameters
        ----------
        json_file_path : str
            file path to JSON file containing CSV template info
        """
        with open(json_file_path, "r", encoding="UTF-8") as fp:
            parser = json.load(fp)
        self.report_type = basename(json_file_path)
        self.columns = parser["columns"]
        self.analysis_columns = parser["analysis_columns"]
        self.set_values_to_index()

    def set_values_to_index(self):
        """If values are ``str``, set to column index"""

        self.analysis_columns["date"] = self.get_index(
            self.analysis_columns["date"]
        )

        for key in ["uid", "criteria"]:
            for i in range(len(self.analysis_columns[key])):
                self.analysis_columns[key][i] = self.get_index(
                    self.analysis_columns[key][i]
                )

        for item in self.analysis_columns["y"]:
            item["index"] = self.get_index(item["index"])

    def get_index(self, value: str or int) -> int:
        """If value is a string, return its index of ``columns``

        Parameters
        ----------
        value : str, int
            any value

        Returns
        -------
        int
            If value from ``analysis_columns`` is a string, return its index
        """
        if isinstance(value, str):
            return self.columns.index(value)
        return value


def import_csv_templates() -> dict:
    """Import CSV Templates

    Returns
    -------
    dict
        keys are parser names and values are ``CSVParser`` objects. If a
        default parser is missing from ``CSV_TEMPLATES_DIR``, load directly
        from ``IQDMPDF``
    """
    parsers = {}
    if isdir(CSV_TEMPLATES_DIR):
        for file in listdir(CSV_TEMPLATES_DIR):
            try:
                key = splitext(file)[0]
                if splitext(file)[1].lower() == ".json":
                    parsers[key] = CSVParser(join(CSV_TEMPLATES_DIR, file))
            except Exception as e:
                msg = f"importer: failed to load {file} as a Parser template"
                push_to_log(e, msg=msg)
    for key, parser in DEFAULT_PARSERS.items():
        if key not in parsers:
            parsers[key] = parser
    return parsers


def create_default_parsers():
    """Generate CSV_TEMPLATE JSON files from IQDMPDF, if it doesn't exist"""
    for key, parser in DEFAULT_PARSERS.items():
        file_path = join(CSV_TEMPLATES_DIR, f"{key}.json")
        if not isfile(file_path):
            create_csv_template(parser())
    copy_default_csv_templates()


def copy_default_csv_templates():
    """Copy default JSON file form resources/csv_templates"""
    existing_templates = listdir(CSV_TEMPLATES_DIR)
    for file in listdir(DEFAULT_CSV_TEMPLATES_DIR):
        if file not in existing_templates:
            try:
                copyfile(
                    join(DEFAULT_CSV_TEMPLATES_DIR, file),
                    join(CSV_TEMPLATES_DIR, file),
                )
            except Exception as e:
                msg = f"paths: failed to copy {file} into {CSV_TEMPLATES_DIR}"
                push_to_log(e, msg=msg)


def create_csv_template(parser: ParserBase):
    """Write a CSV_TEMPLATE to JSON

    Parameters
    ----------
    parser : ParserBase
        a parser from IQDMPDF
    """
    data = {
        "columns": parser.columns,
        "analysis_columns": parser.analysis_columns,
    }
    file_path = join(CSV_TEMPLATES_DIR, f"{parser.report_type}.json")
    try:
        with open(file_path, "w", encoding="UTF-8") as fp:
            fp.write(json.dumps(data, indent=2))
    except Exception as e:
        msg = f"importer: failed to create {file_path}"
        push_to_log(e, msg=msg)


class ReportImporter:
    """Class to import IQDM-PDF CSV output"""

    def __init__(
        self, report_file_path: str, parser: str, duplicate_detection: bool
    ):
        """Initialize ``ReportImporter``

        Parameters
        ----------
        report_file_path : str
            File path to CSV output from IQDM-PDF
        parser : str
            The parser used to generate the report. Either 'SNCPatient2020',
            'SNCPatientCustom', 'Delta4', 'Verisoft', 'VarianPortalDosimetry'
        duplicate_detection : bool
            If true, apply a multi_value policy from options

        """
        self.data_dict = csv_to_dict(report_file_path)

        self.parser = import_csv_templates()[parser]
        self.columns = self.parser.columns
        self.analysis_columns = self.parser.analysis_columns
        self.duplicate_detection = duplicate_detection
        self.re_non_decimal = re.compile(r"[^\d.]+")

    @property
    def uid_col(self) -> list:
        """Column names, when combined create a UID

        Returns
        -------
        list
            Column names from ``analysis_columns['uid']``
        """
        if self.duplicate_detection:
            return [self.columns[i] for i in self.analysis_columns["uid"]]
        return list(set(self.columns) - set(self.criteria_col))

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

    def remove_non_numeric(self, val: str) -> float:
        """Remove all non-numeric characters, convert to float, use to
        highjack ``dtype`` in ``widen_data``

        Parameters
        ----------
        val : str
            Any string

        Returns
        -------
        float
            ``val`` converted into a float
        """

        val = self.re_non_decimal.sub("", val)
        try:
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

        kwargs = {
            "uid_columns": self.uid_col,
            "x_data_cols": self.criteria_col,
            "y_data_col": charting_column,
            "date_col": self.columns[self.analysis_columns["date"]],
            "dtype": self.remove_non_numeric,
            "date_col_file_creation": "report_file_creation",
            "multi_val_policy": multi_val_policy,
        }
        data = widen_data(self.data_dict, **kwargs)
        x_axis = data.pop("date")
        uids = data.pop("uid")

        return {"data": data, "x_axis": x_axis, "uids": uids}
