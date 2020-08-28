#!/usr/bin/env python
# -*- coding: utf-8 -*-
# stats.py
"""Statistical calculations for the IQDM-Analytics repository."""
# Copyright (c) 2020 Dan Cutright
# Copyright (c) 2020 Arka Roy
# This file is part of AAPM IMRT QA Data Mining project
# https://iqdm.github.io/

from os.path import isfile, splitext
import numpy as np
from scipy.stats import beta
from utilities import dict_to_array, csv_to_dict


class PassRateStats:
    def __init__(self, data, var_names=None):
        """Class used to calculated various statistics

        Parameters
        ----------
        data : numpy.array, dict, str
            Input data (2-D) with N rows of observations and
            p columns of variables.  The CSV file must have a header row
            for column names.
        var_names : list of str, optional
            If data is a numpy array, optionally provide the column names.

        """
        if isinstance(data, np.ndarray):
            self.data = data
            self.var_names = var_names
        elif isinstance(data, dict):
            data = dict_to_array(data)
            self.data = data["data"]
            self.var_names = data["var_names"]
        elif isfile(data) and splitext(data)[1] == ".csv":
            data = dict_to_array(csv_to_dict(data, dtype=float))["data"]
            self.data = data["data"]
            self.var_names = data["var_names"]
        else:
            msg = (
                "Invalid data provided - "
                "must be a numpy array, dict, or .csv file"
            )
            raise NotImplementedError(msg)

    @property
    def observations(self):
        """Number of observations"""
        return self.data.shape[0]

    @property
    def variables(self):
        """Number of variables"""
        return self.data.shape[1]

    def hotelling_t2(self, signifiance):
        """Calculate Hotelling T^2

        Parameters
        ----------
        signifiance : float
            The significance level used to calculated the
            upper control limit (UCL)

        Returns
        ----------
        dict
            The Hotelling T^2 values (Q), center line (CL),
            and upper control limit (UCL)

        """
        x_cl = 0.5
        x_ucl = 1 - signifiance / 2
        return {
            "Q": hotelling_t2(self.data),
            "CL": hotelling_t2_control_limit(
                x_cl, self.observations, self.variables
            ),
            "UCL": hotelling_t2_control_limit(
                x_ucl, self.observations, self.variables
            ),
        }


def hotelling_t2(arr):
    """Calculate Hotelling T^2 from a numpy array

    Parameters
    ----------
    arr : np.array
        A numpy array with N rows (observations) and p columns (variables)

    Returns
    -------
    np.array
        A numpy array of Hotelling T^2 (1-D of length N)
    """
    Q = np.zeros(np.size(arr, 0))
    D_bar = np.mean(arr, axis=0)
    S = np.cov(arr.T)
    S_inv = np.linalg.inv(S)
    observations = np.size(arr, 0)
    for i in range(observations):
        spread = arr[i, :] - D_bar
        Q[i] = np.matmul(np.matmul(spread, S_inv), spread)
    return Q


def hotelling_t2_control_limit(x, observations, variables):
    """Calculate a Hotelling T^2 control limit using a beta distribution

    Parameters
    ----------
    x : float
        Value where the beta function is evaluated
    observations : int
        Number of observations in the sample
    variables : int
        Number of variables observed for each sample

    Returns
    -------
    float
        The control limit for a beta distribution using the provided parameters
    """

    N = observations
    a = variables / 2
    b = (N - variables - 1) / 2
    return ((N - 1) ** 2 / N) * beta.ppf(x, a, b)
