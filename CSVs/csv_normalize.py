""" 'Normalize' a CSV file, so that it can be compared
(using a difference utility like WinMerge)
with another CSV file which has different formatting, different column ordering,
different column naming, added/subtracted columns, and/or (non-)collapsed columns.
"""

import csv
import os
import re

# pip-installed
from csvsort import csvsort


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


def normalize_numbers_and_dates(row):

    # TODO Add an option to allow the "decimal comma" as alternative decimal separator.
    #      See Wikipedia's wiki/Decimal_separator#Countries_using_decimal_comma

    new_row = []
    for column in row:

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

    return new_row


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


# def csv_sort(csv_file, sorted_csv_file, reverse=False):

#     # Sort input file csv_file to create output file sorted_csv_file

#     with open(csv_file, "r") as read_file, open(sorted_csv_file, "w") as write_file:
#         rows = read_file.readlines()
#         rows = [rows[0]] + sorted(rows[1:], reverse=reverse)
#         #   Sort non-header rows (leaving header row intact)
#         write_file.writelines(rows)


def do_csv_normalize(
    path, inp, column_renames=None, column_collapse_pairs=None, new_columns=None
):

    os.chdir(path)
    (root, ext) = os.path.splitext(inp)
    out = f"{root}_2{ext}"

    with open(inp, newline="") as inp_file, open(out, mode="w", newline="") as out_file:

        # Note that when the inp_file doesn't have a trailing blank line,
        # this inserts one. Apparently, it's normal for csv files to have one.

        reader = csv.reader(inp_file)
        writer = csv.writer(out_file)

        for index, row in enumerate(reader):

            if index:  # index != 0; row is not a row of column header row

                new_row = normalize_numbers_and_dates(row)

                if column_collapse_pairs is not None:
                    new_row = collapse_columns(new_row, column_collapse_pairs)
                if new_columns is not None:
                    new_row = reorder_columns_in_row(new_row, new_columns)
                writer.writerow(new_row)

            else:  # index == 0; row is a column header row

                if column_renames is not None:
                    row = rename_columns(row, column_renames)
                if new_columns is not None:
                    row = reorder_columns_in_row(row, new_columns)
                writer.writerow(row)

    # Sort this CSV on the 1st (0-indexed) column
    #
    # With python 3.8.2 in Windows 8.1 Pro, pip-installed module csvsort gave errors
    # even on its 1st demo program. (See test_csvsort in my private Python Playground.)

    # csv_sort(out, f"{root}_3{ext}", reverse=True)
    csvsort(out, [0, 1])  # PyPi csvsort module has been fixed to work with Python 3.8.3


def main():
    pass  # TODO: Put example usage here


if __name__ == "__main__":
    main()
