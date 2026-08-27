#!/usr/bin/env -S .venv/bin/python
import csv
import os
import shutil
import subprocess
import re
import sys

def get_valid_number(prompt, num_type="float", allow_blank=True):
    """Prompts the user until a valid number (or blank) is entered."""
    while True:
        val = input(prompt).strip()
        if allow_blank and not val:
            return val
        
        try:
            if num_type == "float":
                float(val)
            else:
                int(val)
            return val
        except ValueError:
            print(f"  -> Error: Must be a valid {num_type}. Try again.")

def main():
    csv_file = "atlCSV.csv"
    backup_file = "atlCSV_backup.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Ensure you are in the correct directory.")
        return

    # 1. Create a safe backup before modifying
    shutil.copy2(csv_file, backup_file)
    
    print("=========================================")
    print("      Storm Surge Data Entry Tool        ")
    print("=========================================")
    print(f"* Backup created as {backup_file}")
    print("* Press Ctrl+C at any time to cancel without saving.")
    print("-----------------------------------------\n")
    
    entry_type = input("Are you adding a [S]torm or a [Y]ear spacer? (S/Y): ").strip().upper()

    if entry_type == 'Y':
        # Fast-track spacer creation
        y_val = get_valid_number("Year (YYYY) for spacer: ", "int", allow_blank=False)
        new_row = {
            "YYYY": y_val, "Storm": "", "Retire?": "", "Wikipedia": "", 
            "Date": "", "Cat": "", "Pres": "", "Dead": "", 
            "$bn": "", "minStmTide": "", "maxStmTide": "0", "TCR or Ref.": "", 
            "FEV": "", "Guidance": "", "Area": ""
        }
    else:
        # Standard storm prompts
        print("Leave a field blank and press Enter to skip.\n")
        new_row = {
            "YYYY": get_valid_number("Year (YYYY): ", "int", allow_blank=False),
            "Storm": input("Storm Name: ").strip(),
            "Retire?": input("Retired? (Yes/No): ").strip().title(),
            "Wikipedia": input("Wikipedia URL: ").strip(),
            "Date": input("Date (e.g., Jul 31-Aug 4): ").strip(),
            "Cat": input("Category (e.g., 4): ").strip(),
            "Pres": get_valid_number("Pressure (mb): ", "int"),
            "Dead": input("Deaths: ").strip(),
            "$bn": get_valid_number("Damage ($bn): ", "float"),
            "minStmTide": get_valid_number("Min Storm-Tide/Surge (ft, optional): ", "float", allow_blank=True),
            "maxStmTide": get_valid_number("Peak Storm-Tide/Surge (ft, max value): ", "float", allow_blank=False),
            "TCR or Ref.": input("NOAA TCR URL: ").strip(),
            "FEV": input("USGS FEV URL: ").strip(),
            "Guidance": input("Guidance (e.g., P-Surge): ").strip(),
            "Area": input("Impact Area: ").strip()
        }

    # 2. Read existing data and get ORIGINAL headers
    with open(csv_file, mode="r", encoding="utf-8") as read_file:
        reader = csv.DictReader(read_file)
        original_headers = reader.fieldnames
        rows = list(reader)

    # 3. Append new row
    rows.append(new_row)

    # 4. Filter and Sort Rows
    clean_rows = []
    for r in rows:
        # Keep row if at least one column has text (strips out entirely blank rows)
        if any(str(v).strip() for v in r.values() if v is not None):
            clean_rows.append(r)

    def get_sort_key(row):
        year_str = str(row.get("YYYY", "")).strip()
        year = int(year_str) if year_str.isdigit() else -1
        
        # If there is no storm name, treat it as a Year Spacer (floats to top of year)
        if not str(row.get("Storm", "")).strip():
            return (year, 13, 32) 
            
        date_str = str(row.get("Date", "")).lower()
        month_val = 0
        day_val = 0
        
        # Scans left-to-right and grabs the FIRST month it encounters
        month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', date_str)
        if month_match:
            months = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
            }
            month_val = months[month_match.group(1)]
                
        # Grabs the FIRST number it encounters as the day
        day_match = re.search(r'\d+', date_str)
        if day_match:
            day_val = int(day_match.group())
            
        return (year, month_val, day_val)

    # Sort descending: newest Year first -> newest Month -> newest Day
    clean_rows.sort(key=get_sort_key, reverse=True)

    # 5. Write everything back using the ORIGINAL column order
    # Failsafe: if the prompt asked for a new column not in the old CSV, append it so we don't lose data
    for key in new_row.keys():
        if key not in original_headers:
            original_headers.append(key)

    with open(csv_file, mode="w", newline="", encoding="utf-8") as write_file:
        writer = csv.DictWriter(write_file, fieldnames=original_headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(clean_rows)
        
    identifier = new_row['YYYY'] if entry_type == 'Y' else f"{new_row['Storm']} ({new_row['YYYY']})"
    print(f"\n✅ Success: {identifier} added. CSV cleaned, sorted, and saved.")

    # 6. Automatically trigger the table generation script
    print("Generating updated markdown table...")
    try:
        with open("README.md", "w") as readme_file:
            subprocess.run(["./generate_table.py"], stdout=readme_file, check=True)
        print("✅ Done! README.md has been updated.")
    except Exception as e:
        print(f"Error running generate_table.py: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # This catches the Ctrl+C gracefully and hides the traceback
        print("\n\n🚫 Data entry cancelled by user. No changes were saved to the CSV.")
        sys.exit(0)
