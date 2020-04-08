""" 'Normalize' a CSV file, so that it can be compared
(using a difference utility like WinMerge)
with another CSV file which has different formatting, different column ordering,
different column naming, added/subtracted columns, and/or (non-)collapsed columns.
"""

import csv
import enum
import os
import re

class ColumnOptionsType(enum.Enum):
    column_renames = 1
    column_collapse_pairs = 2
    new_columns = 3

def normalize_date(column):

    # TODO: Add option to reverse the order of month and day.

    pattern = r"^(\d{1,2})\/(\d{1,2})\/(\d{4})$"
    match = re.search(pattern, column)
    if match:  # Convert 01/02/2020 to 1/2/20
        month = match.group(1).lstrip("0")
        day = match.group(2).lstrip("0")
        year = match.group(3)[2:]
        column = f"{month}/{day}/{year}"

    else:  # Convert 2020-01-02 to 1/2/20
        pattern = r"^(\d{4})\-(\d{1,2})\-(\d{1,2})$"
        match = re.search(pattern, column)
        if match:
            year = match.group(1)[2:]
            month = match.group(2).lstrip("0")
            day = match.group(3).lstrip("0")
            column = f"{month}/{day}/{year}"

    return column

def reorder_columns_in_row(row, arg_new_columns):

    # new_columns is a list of (optionally re-ordered) columns to include in the output.

    # For example, if the CSV has 13 columns (0 to 12), then to:
    #   Omit columns 4, 6, 8, 10, and 12
    # and
    #   Reverse the order of columns 5 and 7
    # specify:
    #   new_columns = [0, 1, 2, 3, 7, 5, 9, 11]

    reordered_row = []
    for column in arg_new_columns:
        reordered_row.append(row[column])

    return reordered_row


def rename_columns(row, arg_column_renames):

    # arg_column_renames is a list of column renaming pairs

    # For example, to rename column "Name1" to "First Name",
    # and column "Name2" as "Last Name", specify:
    #   arg_column_renames = [("Name1", "First Name"), ("Name2", "Last Name")]

    new_row = []
    for column in row:
        for column_rename in arg_column_renames:
            column = column.replace(column_rename[0], column_rename[1])
        new_row.append(column)

    return new_row


def collapse_columns(row, column_collapse_pairs):

    # column_collapse_pairs is a list of pairs of columns to "collapse" into 1 column
    # (when their values are equal).

    # For example, to do:
    #   row[2] = "" if (row[1] == row[2]) else row[2]
    # specify:
    #   column_collapse_pairs = [(1, 2)]

    for pair in column_collapse_pairs:
        row[pair[1]] = "" if (row[pair[0]] == row[pair[1]]) else row[pair[1]]

    return row


def csv_sort(csv_file, sorted_csv_file, reverse=False):

    # Sort input file csv_file to create output file sorted_csv_file

    with open(csv_file, "r") as read_file, open(sorted_csv_file, "w") as write_file:
        rows = read_file.readlines()
        rows = [rows[0]] + sorted(rows[1:], reverse=reverse)
        #   Sort non-header rows (leaving header row intact)
        write_file.writelines(rows)

def do_csv_normalize(
    path,
    inp,
    out,
    out_sorted,
    column_options = None
):
    """ 
    
    In order to avoid prospector linter's "pylint(too-many-arguments)" error,
    I have consolidated 3 separate, but related arguments
    (column_renames, column_collapse_pairs, and new_columns) into 1.

    column_options is a dict which may specify values for 1 or more of the following keys:
        column_renames, column_collapse_pairs, and/or new_columns
    """

    # Avoid "warning| Dangerous default value [] as argument"
    if column_options is None:
        column_options = {}

    os.chdir(path)
    with open(inp, newline="") as inp_file, open(out, mode="w", newline="") as out_file:

        # Note that when the inp_file doesn't have a trailing blank line,
        # this inserts one. Apparently, it's normal for csv files to have one.

        reader = csv.reader(inp_file)
        writer = csv.writer(out_file)

        for index, row in enumerate(reader):

            if index:  # index != 0; row is not a row of column header row
                new_row = []
                for column in row:

                    # TODO Add option to allow the "decimal comma" as alternative decimal
                    #      separator. See Wikipedia's
                    #           wiki/Decimal_separator#Countries_using_decimal_comma
                    pattern = r"^\-{0,1}\d{1,}\.\d{0,}0$"
                    match = re.search(pattern, column)
                    if match:  # column is a decimal number ending in 0
                        # Omit any trailing zeros, and then any trailing decimal point
                        column = column.rstrip("0").rstrip(".")

                    pattern = r"^\-0$"
                    match = re.search(pattern, column)
                    if match:  # column value is negative 0
                        column = "0"  # Replace with a non-negative 0
                        
                    else:
                        column = normalize_date(column)  # if column's a date, normalize it

                    new_row.append(column)

                if ColumnOptionsType.column_collapse_pairs in column_options:
                    new_row = collapse_columns(new_row, column_options[ColumnOptionsType.column_collapse_pairs])
                if ColumnOptionsType.new_columns in column_options:
                    new_row = reorder_columns_in_row(new_row, column_options[ColumnOptionsType.new_columns])
                writer.writerow(new_row)
            else:  # index == 0; row is a column header row
                if ColumnOptionsType.column_renames in column_options:
                    row = rename_columns(row, column_options[ColumnOptionsType.column_renames])
                if ColumnOptionsType.new_columns in column_options:
                    row = reorder_columns_in_row(row, column_options[ColumnOptionsType.new_columns])
                writer.writerow(row)

    # Sort this CSV on the 1st (0-indexed) column
    #
    # With python 3.8.2 in Windows 8.1 Pro, pip-installed module csvsort gives errors
    # even on its 1st demo program. (See test_csvsort in my private Python Playground.)
    # So, I've replaced:
    #   csvsort(out, [1, 2])
    # with:
    csv_sort(out, out_sorted, reverse=True)


def main():
    pass  # TODO: Put example usage here


if __name__ == "__main__":
    main()
