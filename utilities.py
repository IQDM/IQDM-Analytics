#!/usr/bin/env python
# -*- coding: utf-8 -*-
# utilities.py
"""Common functions for the IQDM-Analytics repository."""
# Copyright (c) 2020 Dan Cutright
# This file is part of AAPM IMRT QA Data Mining project
# https://iqdm.github.io/

import numpy as np


def csv_to_dict(csv_file_path, dtype=None):
    """Read in a csv file, return data as a dictionary

    Parameters
    ----------
    csv_file_path : str
        File path to the CSV file to be processed.
    dtype : None, Type, optional
        Optionally force values to a type (e.g., float, int, str, etc.).

    Returns
    -------
    dict
        CSV data as a dict, using the first row values as keys
    """

    with open(csv_file_path) as fp:
        keys = fp.readline().strip().split(",")
        data = {key: [] for key in keys}
        for line in fp:
            row = line.strip().split(",")
            for i, value in enumerate(row):
                if dtype is not None:
                    value = dtype(value)
                data[keys[i]].append(value)
    return data


def dict_to_array(data, key_order=None):
    """Convert a dict of data to a numpy array

    Parameters
    ----------
    data : dict
        File path to the CSV file to be processed.
    key_order : None, list of str
        Optionally the order of columns

    Returns
    -------
    dict
        A dictionary with keys of 'data' and 'columns', pointing to a
        numpy array and list of str, respectively
    """
    var_names = key_order if key_order is not None else list(data.keys())
    arr_data = [data[key] for key in var_names]
    return {"data": np.asarray(arr_data).T, "var_names": var_names}
