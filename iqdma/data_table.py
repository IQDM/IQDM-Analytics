#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# data_table.py
"""
A class to sync a data object and list_ctrl
"""
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM-Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/IQDM/IQDM-Analytics

from copy import deepcopy
import wx
from iqdma.utilities import get_selected_listctrl_items, get_sorted_indices


class DataTable:
    """Helper class for ``wx.ListCtrl``"""

    def __init__(
        self,
        list_ctrl: wx.ListCtrl,
        data: dict = None,
        columns: list = None,
        widths: list = None,
        formats: list = None,
    ):
        """Init DataTable class

        Parameters
        ----------
        list_ctrl : wx.ListCtrl
            the list_ctrl in the GUI to be updated with data in this class
        data : dict
            data should be formatted in a dictionary with keys being the
            column names and values being lists
        columns : list
            the keys of the data object to be visible in the list_ctrl
        widths : list
            optionally specify the widths of the columns
        formats : list
            optionally specify wx Format values (e.g., wx.LIST_FORMAT_LEFT)

        """

        self.layout = list_ctrl

        self.sort_indices = None

        self.data = deepcopy(data)
        self.columns = deepcopy(columns)
        self.widths = widths
        if formats:
            self.formats = formats
        else:
            if not self.columns:
                column_length = 0
            else:
                column_length = len(self.columns)
            self.formats = [wx.LIST_FORMAT_LEFT] * column_length
        if data:
            # TODO: Initializing class with duplicates data in view?
            self.set_data(data, columns, formats=formats)
        self.set_data_in_layout()

    def set_data(
        self,
        data: dict,
        columns: list,
        formats: list = None,
        ignore_layout: bool = False,
    ):
        """Set data and update layout

        Parameters
        ----------
        data : dict
            data should be formatted in a dictionary with keys being the
            column names and values being lists
        columns : list
            the keys of the data object to be visible in the list_ctrl
        formats : list
            optionally specify wx Format values (e.g., wx.LIST_FORMAT_LEFT)
        ignore_layout : bool
            If true, do not update layout

        """
        if formats:
            self.formats = formats
        elif columns and len(columns) != len(self.formats):
            self.formats = [wx.LIST_FORMAT_LEFT] * len(columns)

        delete_rows = bool(self.row_count)
        self.data = deepcopy(data)
        self.columns = deepcopy(columns)
        if delete_rows:
            self.delete_all_rows(layout_only=True)

        if not ignore_layout:
            self.set_layout_columns()
            self.set_data_in_layout()

        if self.widths:
            self.set_column_widths()

        # If len of new data is different than previous, sorting may crash
        self.sort_indices = None

    def set_layout_columns(self):
        """Clear layout and re-add columns"""
        self.layout.DeleteAllColumns()
        for i, col in enumerate(self.columns):
            self.layout.AppendColumn(col, format=self.formats[i])

    @property
    def keys(self) -> list:
        """Column names

        Returns
        -------
        list
            A copy of ``columns``
        """
        return [col for col in self.columns]

    @property
    def column_count(self) -> int:
        """Number of columns

        Returns
        -------
        int
            Length of ``columns``

        """
        if self.columns:
            return len(self.columns)
        return 0

    @property
    def row_count(self) -> int:
        """Number of rows

        Returns
        -------
        int
            Length of first column in ``data``

        """
        if self.data:
            return len(self.data[self.columns[0]])
        return 0

    def data_to_list_of_rows(self) -> list:
        """Convert ``data`` into a list of rows as needed for list_ctrl

        Returns
        -------
        list
            data in the format of list of rows

        """
        if self.data and self.keys:
            return [
                [self.data[col][row] for col in self.columns]
                for row in range(self.row_count)
            ]
        else:
            return []

    def set_data_in_layout(self):
        """Set data in layout from ``data``"""
        row_data = self.data_to_list_of_rows()

        for row in row_data:
            self.append_row(row, layout_only=True)

    def append_row(self, row: list, layout_only: bool = False):
        """Add a row of data

        Parameters
        ----------
        row : list
            data ordered by self.columns
        layout_only : bool
            If true, only add row to the GUI

        """
        if not layout_only:
            self.append_row_to_data(row)
        if self.layout:
            index = self.layout.InsertItem(50000, str(row[0]))
            for i in range(len(row))[1:]:
                if isinstance(row[i], int):
                    value = "%d" % row[i]
                elif isinstance(row[i], float):
                    value = "%0.2f" % row[i]
                else:
                    value = str(row[i])
                self.layout.SetItem(index, i, value)

    def append_row_to_data(self, row: list):
        """Add a row of data to self.data

        Parameters
        ----------
        row : list
            data ordered by self.columns

        """
        if not self.data:
            columns = self.keys
            self.data = {columns[i]: [value] for i, value in enumerate(row)}
        else:
            for i, key in enumerate(self.keys):
                self.data[key].append(row[i])

    def delete_all_rows(
        self, layout_only: bool = False, force_delete_data: bool = False
    ):
        """Clear all data from ``data`` and the layout view

        Parameters
        ----------
        layout_only : bool
            If True, do not remove the row from self.data
        force_delete_data : bool
            If true, force deletion even if layout is not set

        """
        if self.layout:
            self.layout.DeleteAllItems()

        if self.layout or force_delete_data:
            if not layout_only:
                if self.data:
                    for key in self.keys:
                        self.data[key] = []

    def get_value(self, row_index: int, column_index: int):
        """Get a specific table value with a column name and row index

        Parameters
        ----------
        row_index : int
            retrieve value from row with this index
        column_index : int
            retrieve value from column with this index

        Returns
        -------
        any
            value corresponding to provided indices

        """
        return self.data[self.keys[column_index]][row_index]

    def get_row(self, row_index: int) -> list:
        """Get a row of data from self.data with the given row index

        Parameters
        ----------
        row_index : int
            retrieve all values from row with this index

        Returns
        -------
        list
            values for the specified row

        """
        return [self.data[key][row_index] for key in self.keys]

    def set_column_width(self, index: int, width: int):
        """Change the column width in the view

        Parameters
        ----------
        index : int
            index of column
        width : int
            the specified width

        """
        self.layout.SetColumnWidth(index, width)

    def set_column_widths(self, auto: bool = False):
        """Set all widths in layout based on ``widths``

        Parameters
        ----------
        auto : bool
            Use ``wx.LIST_AUTOSIZE_USEHEADER`` rather than ``widths``
        """
        if auto:
            for i in range(len(self.columns)):
                self.set_column_width(i, wx.LIST_AUTOSIZE_USEHEADER)
        else:
            if self.widths is not None:
                for i, width in enumerate(self.widths):
                    self.set_column_width(i, width)

    def clear(self):
        """Delete all data in self.data and clear the table view"""
        self.delete_all_rows()
        self.layout.DeleteAllColumns()

    def get_csv_rows(self) -> list:
        """Convert ``data`` to a list of strings for CSV writing

        Returns
        -------
        list of str
            Each item is a str for a CSV file
        """

        csv_data = []
        for row in self.data_for_csv:
            row = [str(el).replace("\n", "<>") for el in row]
            csv_data.append(",".join(row))

        return csv_data

    @property
    def data_for_csv(self) -> list:
        """Iterate through ``data`` to get a list of csv rows

        Returns
        -------
        list of lists
            list of rows. Each row is a list of column data

        """
        data = [self.columns]
        for row_index in range(self.row_count):
            row = []
            for key in self.keys:
                raw_value = self.data[key][row_index]
                if isinstance(raw_value, float):
                    row.append("%0.5f" % raw_value)
                else:
                    row.append(raw_value)
            data.append(row)
        return data

    @property
    def selected_row_data(self) -> list:
        """Row data from the current selection in ``wx.ListCtrl``

        Returns
        -------
        list
            row data of the currently selected row in the GUI

        """
        return [
            self.get_row(index)
            for index in get_selected_listctrl_items(self.layout)
        ]

    @property
    def selected_row_index(self) -> list:
        """Get the indices of selected rows in ``wx.ListCtrl``

        Returns
        -------
        list
            List of indices
        """
        return get_selected_listctrl_items(self.layout)

    @property
    def has_data(self) -> bool:
        """Check if there are any rows of data

        Returns
        -------
        bool
            True if ``row_count`` > 0
        """
        return bool(self.row_count)

    def sort_table(self, evt: wx.EVT_LIST_COL_CLICK):
        """Sort the data based on the clicked column header

        Parameters
        ----------
        evt : wx.EVT_LIST_COL_CLICK
            Event from a ListCtrl column header click
        """

        if self.data:
            key = self.columns[
                evt.Column
            ]  # get the column name from the column index (evt.Column)
            sort_indices = get_sorted_indices(
                self.data[key]
            )  # handles str and float mixtures

            if self.sort_indices is None:
                self.sort_indices = list(range(len(self.data[key])))

            # reverse order if already sorted
            if sort_indices == list(range(len(sort_indices))):
                sort_indices = sort_indices[::-1]

            self.sort_indices = [
                self.sort_indices[i] for i in sort_indices
            ]  # keep original order

            # reorder data and reinitialize table view
            self.data = {
                column: [self.data[column][i] for i in sort_indices]
                for column in self.columns
            }
            self.set_data(self.data, self.columns, self.formats)

    def get_data_in_original_order(self) -> dict:
        """Get ``data`` in the order it was original set

        Returns
        -------
        dict
            keys are column names with voalues of row data
        """
        if self.sort_indices is None:
            return self.data
        return {
            column: [self.data[column][i] for i in self.sort_indices]
            for column in self.columns
        }

    def increment_index(self, evt: wx.Event = None, increment: int = None):
        """Increment the ListCtrl selection with an event or fixed increment

        Parameters
        ----------
        evt : wx.Event
            An event with a ``GetKeyCode`` method
        increment : int
            If no event is passed, use a fixed index increment

        """
        if self.has_data:
            if hasattr(evt, "GetKeyCode"):
                keycode = evt.GetKeyCode()

                if keycode == wx.WXK_UP:
                    evt.Skip()
                    increment = -1

                elif keycode == wx.WXK_DOWN:
                    evt.Skip()
                    increment = 1

                else:
                    return

            if increment is None:
                increment = 1

            current_index = self.selected_row_index
            if len(current_index):
                new_index = current_index[0] + increment
                if new_index > self.row_count - 1:
                    new_index = 0
            else:
                new_index = -1 + increment if increment > 0 else -increment
            self.layout.Select(new_index)
