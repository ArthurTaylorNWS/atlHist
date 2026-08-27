#!/usr/bin/env -S .venv/bin/python
# -------------------------------------------------------------------------------
# @file         generate_table.py
# @author       Arthur.Taylor (NWS/OMD/MDSD)
# @description  Parses the Atlantic storm CSV and generates markdown tables.
# -------------------------------------------------------------------------------

import math
import os
import sys
import traceback


def exception_handler(exc_type, exc_value, tb):
    tb_info = traceback.extract_tb(tb)[-1]
    line_num = tb_info.lineno
    print(f"Error on line {line_num}: {exc_value}", file=sys.stderr)
    sys.exit(1)


sys.excepthook = exception_handler


try:
    import pandas as pd
except ImportError:
    print("Error: The 'pandas' library is required.", file=sys.stderr)
    print("Run: .venv/bin/python -m pip install pandas", file=sys.stderr)
    sys.exit(1)


def format_storm_name(row):
    if pd.isna(row.get("Storm")) or not str(row["Storm"]).strip():
        return ""
    year = int(row["YYYY"]) if pd.notna(row["YYYY"]) else ""
    storm = str(row["Storm"]).strip()
    name = f"{year}-{storm}"

    if pd.notna(row.get("Retire?")) and str(row["Retire?"]).strip().lower() == "yes":
        name += " (R)"

    if pd.notna(row.get("Wikipedia")) and str(row["Wikipedia"]).strip():
        return f"[{name}]({row['Wikipedia']})"
    return name


def format_stats(row):
    cat = row["Cat"] if pd.notna(row.get("Cat")) else ""
    pres = int(row["Pres"]) if pd.notna(row.get("Pres")) else ""
    dead = row["Dead"] if pd.notna(row.get("Dead")) else ""
    bn = row["$bn"] if pd.notna(row.get("$bn")) else ""
    return f"({cat}, {pres}, {dead}, {bn})"


def format_surge(row):
    surge = row.get("maxStmTide")
    if pd.notna(surge):
        try:
            w_cat = math.ceil(float(surge) / 3.0)
            return f"w{w_cat}: {surge} surge"
        except (ValueError, TypeError):
            return f"{surge} surge"
    return ""


def format_link(text, url):
    if pd.notna(url) and str(url).strip():
        return f"[{text}]({url})"
    return ""


def main():
    csv_file = "atlCSV.csv"
    if not os.path.exists(csv_file):
        for fallback in ["HistStm2 - atlCSV.csv", "historic/atlCSV.csv", "historic/HistStm2 - atlCSV.csv"]:
            if os.path.exists(fallback):
                csv_file = fallback
                break

    if not os.path.exists(csv_file):
        print("Error: Could not locate storm surge CSV file.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_file)
    df["YYYY"] = pd.to_numeric(df["YYYY"], errors="coerce")
    df["maxStmTide"] = pd.to_numeric(df["maxStmTide"], errors="coerce")

    # Filter master dataframe
    df_filtered = df[(df["YYYY"] >= 1900) & (df["YYYY"] <= 2026)].copy()
    df_filtered = df_filtered.sort_values(by=["YYYY"], ascending=[False])

    # ===== YAML FRONT MATTER =====
    print("---")
    print("layout: default")
    print("title: Atlantic Storm Surge Database (1900-2026)")
    print("permalink: /")
    print("---\n")

    # ===== EXECUTIVE SUMMARY GRID (10-Column Decade Matrix) =====
    print("### Worst Storm Surge Events in the Atlantic (1900-2026)\n")
    print('<div class="decade-summary-table" markdown="1">\n')
    
    df_worst = df_filtered[df_filtered['maxStmTide'] > 6.0]
    
    # 10 columns, 0 through 9
    print("| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |")
    print("|---|---|---|---|---|---|---|---|---|---|")

    # Loop backwards from the 2020s down to the 1900s
    for decade in range(2020, 1890, -10):
        row_cells = []
        
        for year_digit in range(10):
            year = decade + year_digit
            cell_content = f"**{year}**" # Every cell starts with the year
            
            # Only process storms for years up to 2026
            if year <= 2026:
                year_storms = df_worst[df_worst["YYYY"] == year]
                
                if not year_storms.empty:
                    storm_links = []
                    for _, row in year_storms.iterrows():
                        storm_val = str(row["Storm"]).strip()
                        is_retired = str(row.get("Retire?")).strip().lower() == "yes"
                        w_cat = math.ceil(float(row["maxStmTide"]) / 3.0)
                        
                        # Format as Storm-R (w#) or Storm (w#)
                        display_name = f"{storm_val}-R (w{w_cat})" if is_retired else f"{storm_val} (w{w_cat})"
                        
                        # Create the anchor link
                        anchor_id = f"{year}-{storm_val.lower()}"
                        link = f'<a href="#{anchor_id}">{display_name}</a>'
                        storm_links.append(link)
                    
                    # Append the storm links with <br> separators
                    cell_content += "<br>" + "<br>".join(storm_links)
            
            row_cells.append(cell_content)
                
        print("| " + " | ".join(row_cells) + " |")
        
    print('\n</div>\n<hr>\n')

    # ===== DETAILED ERA TABLES =====
    eras = [
        (
            2017, 2026, "2017–2026: The Watch/Warning Era", 
            "In 2017, the NHC officially began issuing Storm Surge Watches and Warnings. [See History](/docs/history/).", 
            ["NOAA", "USGS", "Guidance", "Area"]
        ),
        (
            2012, 2016, "2012–2016: The AGL Transition", 
            "Starting in 2012, NHC Tropical Cyclone Reports shifted to reporting peak water levels as Above Ground Level (AGL). [See Bibliography](/docs/bibliography/).", 
            ["NOAA", "USGS", "Guidance", "Area"]
        ),
        (
            1999, 2011, "1999–2011: Early Guidance & P-Surge", 
            "Captures the introduction of deterministic rexfiles in 1999 through the initial implementation of P-Surge guidance. [See History](/docs/history/).", 
            ["NOAA", "USGS", "Guidance", "Area"]
        ),
        (
            1991, 1998, "1991–1998: The Online TCR Era", 
            "Tropical Cyclone Reports (TCRs) from this era are generally available online. Modern guidance columns are omitted.", 
            ["NOAA", "USGS", "Area"]
        ),
        (
            1954, 1990, "1954–1990: Retired Names & Early Models", 
            "The practice of retiring significant hurricane names began in 1954. Early surge models like SPLASH and SLOSH were introduced in this era. [See Bibliography](/docs/bibliography/).", 
            ["NOAA", "USGS", "Area"]
        ),
        (
            1900, 1953, "1900–1953: Early 20th Century", 
            "Historic surge benchmarks, spanning back to the 1900 Galveston hurricane.", 
            ["NOAA", "Area"]
        )
    ]

    for start_yr, end_yr, title, desc, cols in eras:
        mask_era = (df_filtered["YYYY"] >= start_yr) & (df_filtered["YYYY"] <= end_yr)
        df_era = df_filtered[mask_era]
        
        print(f"### {title}")
        print(f"{desc}\n")
        print('<div class="main-surge-table" markdown="1">\n')
        
        header_row = "| YYYY-Storm | Date | Cat, Pres, Dead, $bn | Storm-Tide |"
        divider_row = "|---|---|---|---|"
        for col in ["NOAA", "USGS", "Guidance", "Area"]:
            if col in cols:
                header_row += f" {col} |"
                divider_row += "---|"
                
        print(header_row)
        print(divider_row)

        current_year = None
        for _, row in df_era.iterrows():
            storm_val = str(row.get("Storm")).strip() if pd.notna(row.get("Storm")) else ""
            if not storm_val or storm_val.lower() == "nan":
                continue

            if current_year and current_year != row["YYYY"]:
                blank_row = "| &nbsp; | | | |" + "".join([" |" for _ in cols])
                print(blank_row)
            current_year = row["YYYY"]

            # Inject the anchor ID into the storm name column
            anchor_id = f'{row["YYYY"]}-{storm_val.lower()}'
            c_name = f'<span id="{anchor_id}"></span>' + format_storm_name(row)
            c_date = str(row["Date"]) if pd.notna(row.get("Date")) else ""
            c_stats = format_stats(row)
            c_surge = format_surge(row)
            c_noaa = format_link("TCR", row.get("TCR or Ref."))
            c_usgs = format_link("FEV", row.get("FEV"))
            c_guide = str(row["Guidance"]) if pd.notna(row.get("Guidance")) else ""
            c_area = str(row["Area"]) if pd.notna(row.get("Area")) else ""

            row_str = f"| {c_name} | {c_date} | {c_stats} | {c_surge} |"
            if "NOAA" in cols: row_str += f" {c_noaa} |"
            if "USGS" in cols: row_str += f" {c_usgs} |"
            if "Guidance" in cols: row_str += f" {c_guide} |"
            if "Area" in cols: row_str += f" {c_area} |"
            print(row_str)
            
        print('\n</div>\n<hr>\n')


if __name__ == "__main__":
    main()
