#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# @file         generate_table.py                        Last Change: 2026-08-26
# @author       Arthur.Taylor (NWS/OMD/MDSD)
# @description  Parses the Atlantic storm CSV and generates a markdown table.
# -------------------------------------------------------------------------------

import math
import sys
import traceback


def exception_handler(exc_type, exc_value, tb):
    """!
    @brief Mimics a Bash 'trap ERR' to provide clean stderr output.
    @param exc_type The type of the exception.
    @param exc_value The exception instance.
    @param tb The traceback object.
    """
    tb_info = traceback.extract_tb(tb)[-1]
    line_num = tb_info.lineno
    print(f"Error on line {line_num}: {exc_value}", file=sys.stderr)
    sys.exit(1)


sys.excepthook = exception_handler


try:
    import pandas as pd
except ImportError:
    print("Error: The 'pandas' library is required.", file=sys.stderr)
    print(
        "Run: source .venv/bin/activate && pip install pandas", file=sys.stderr
    )
    print("That could take 30 seconds or more", file=sys.stderr)
    sys.exit(1)


def format_storm_name(row):
    """!
    @brief Formats the storm name, appending (R) and a wiki link if present.
    @param row A pandas Series representing a single row of storm data.
    @return A formatted string for the storm name column.
    """
    name = f"{int(row['YYYY'])}-{row['Storm']}"
    if str(row["Retire?"]).strip().lower() == "yes":
        name += " (R)"

    if pd.notna(row["Wikipedia"]):
        return f"[{name}]({row['Wikipedia']})"
    return name


def format_stats(row):
    """!
    @brief Formats the stats tuple (Category, Pressure, Dead, $bn).
    @param row A pandas Series representing a single row of storm data.
    @return A formatted string enclosing the stats in parentheses.
    """
    cat = ""
    if pd.notna(row["Cat"]):
        cat = row["Cat"]
    pres = ""
    if pd.notna(row["Pres"]):
        pres = int(row["Pres"])
    dead = ""
    if pd.notna(row["Dead"]):
        dead = row["Dead"]
    bn = ""
    if pd.notna(row["$bn"]):
        bn = row["$bn"]
    return f"({cat}, {pres}, {dead}, {bn})"


def format_surge(row):
    """!
    @brief Calculates the surge index 'w' and formats the output.
    @param row A pandas Series representing a single row of storm data.
    @return A formatted string showing the surge category and value.
    """
    surge = row["maxStmTide"]
    if pd.notna(surge):
        w_cat = math.ceil(float(surge) / 3.0)
        return f"w{w_cat}: {surge} surge"
    return ""


def format_link(text, url):
    """!
    @brief Wraps text in a Markdown link if a valid URL exists.
    @param text The display text for the link.
    @param url The URL string.
    @return A Markdown formatted link, or an empty string.
    """
    if pd.notna(url):
        return f"[{text}]({url})"
    return ""


def main():
    """!
    @brief Main execution block for reading the CSV and printing the table.
    """
    df = pd.read_csv("atlCSV.csv")
    start_year = 2005
    end_year = 2011

    mask = (df["YYYY"] >= start_year) & (df["YYYY"] <= end_year)
    df_filtered = df[mask].copy().sort_values(by=["YYYY"], ascending=[False])

    print(
        f"### Storm Surge Events in the Atlantic from "
        "{end_year} to {start_year}"
    )
    print(
        "Peak Storm Surge 1: <= 3 ft, 2: <= 6 ft, 3: <= 9 ft, 4: <= 12 ft, "
        "5: <= 15 ft, 6: > 15ft\n"
    )
    print(
        "| YYYY-Storm | Date | Cat, Pres, Dead, $bn | Storm-Tide | NOAA | "
        "USGS | Guidance | Area |"
    )
    print("|---|---|---|---|---|---|---|---|")

    current_year = None

    for index, row in df_filtered.iterrows():
        if current_year and current_year != row["YYYY"]:
            print("| &nbsp; | | | | | | | |")
        current_year = row["YYYY"]

        c_name = format_storm_name(row)
        c_date = ""
        if pd.notna(row["Date"]):
            c_date = row["Date"]
        c_stats = format_stats(row)
        c_surge = format_surge(row)
        c_noaa = format_link("TCR", row["TCR or Ref."])
        c_usgs = format_link("FEV", row["FEV"])
        c_guide = ""
        if pd.notna(row["Guidance"]):
            c_guide = row["Guidance"]
        c_area = ""
        if pd.notna(row["Area"]):
            c_area = row["Area"]

        print(
            f"| {c_name} | {c_date} | {c_stats} | {c_surge} | {c_noaa} | "
            "{c_usgs} | {c_guide} | {c_area} |"
        )


if __name__ == "__main__":
    main()
