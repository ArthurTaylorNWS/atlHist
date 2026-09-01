#!/usr/bin/env python3
import csv
import os
import shutil
import subprocess
import re
import sys

def prompt_field(prompt, current_val="", num_type="str", allow_blank=True):
    """Prompts for a field, allowing defaults, overwrites, or clears."""
    if current_val:
        full_prompt = f"{prompt} [{current_val}]: "
    else:
        full_prompt = f"{prompt}: "
        
    while True:
        val = input(full_prompt).strip()
        
        if not val:
            if current_val:
                return current_val
            if allow_blank:
                return ""
            else:
                print("  -> Error: This field cannot be blank.")
                continue
                
        if val.upper() == 'CLEAR':
            if allow_blank:
                return ""
            else:
                print("  -> Error: This field cannot be blank.")
                continue
        
        if num_type != "str":
            try:
                if num_type == "float":
                    float(val)
                elif num_type == "int":
                    int(val)
            except ValueError:
                print(f"  -> Error: Must be a valid {num_type}. Try again.")
                continue
                
        return val

def format_area(area_input):
    """Auto-corrects spelled-out areas to 2/3 letter abbreviations and wraps unknown phrases in {}."""
    AREA_MAP = {
        "FLORIDA": "FL", "NORTH CAROLINA": "NC", "SOUTH CAROLINA": "SC",
        "TEXAS": "TX", "LOUISIANA": "LA", "MISSISSIPPI": "MS", "ALABAMA": "AL",
        "GEORGIA": "GA", "VIRGINIA": "VA", "MARYLAND": "MD", "DELAWARE": "DE",
        "NEW JERSEY": "NJ", "NEW YORK": "NY", "CONNECTICUT": "CT", "RHODE ISLAND": "RI",
        "MASSACHUSETTS": "MA", "NEW HAMPSHIRE": "NH", "MAINE": "ME", "PENNSYLVANIA": "PA",
        "CUBA": "CUB", "JAMAICA": "JAM", "DOMINICAN REPUBLIC": "DOM", "HAITI": "HTI",
        "BAHAMAS": "BHS", "BERMUDA": "BMU", "MEXICO": "MEX", "PUERTO RICO": "PRI",
        "CAPE VERDE": "CPV", "LESSER ANTILLES": "LCA", "HONDURAS": "HND", 
        "NICARAGUA": "NIC", "BELIZE": "BLZ", "CANADA": "CAN"
    }
    
    parts = [p.strip() for p in area_input.split(",")]
    cleaned = []
    
    for p in parts:
        if not p: continue
        upper_p = p.upper()
        
        if upper_p in AREA_MAP:
            # Matched a known state/country
            cleaned.append(AREA_MAP[upper_p])
        elif len(p) <= 3 and p.isupper() and p.isalpha():
            # Already a valid 2 or 3 letter capitalized code
            cleaned.append(p)
        elif p.startswith("{") and p.endswith("}"):
            # Already properly wrapped in brackets
            cleaned.append(p)
        else:
            # Unknown phrase, wrap in {}
            cleaned.append(f"{{{p}}}")
            
    return ", ".join(cleaned)

FIELD_DEFS = [
    ("YYYY", "Year (YYYY)", "int", False),
    ("Storm", "Storm Name", "str", False),
    ("Retire?", "Retired? (Yes/No)", "str", True),
    ("Wikipedia", "Wikipedia URL", "str", True),
    ("Date", "Date (e.g., Jul 31-Aug 4)", "str", True),
    ("Cat", "Category (e.g., 4)", "str", True),
    ("Pres", "Pressure (mb)", "int", True),
    ("Dead", "Deaths", "str", True),
    ("$bn", "Damage ($bn)", "float", True),
    ("minStmTide", "Min Storm-Tide/Surge (ft, optional)", "float", True),
    ("maxStmTide", "Peak Storm-Tide/Surge (ft, max value)", "float", True),
    ("TCR or Ref.", "NOAA TCR URL", "str", True),
    ("FEV", "USGS FEV URL", "str", True),
    ("Guidance", "Guidance (e.g., P-Surge)", "str", True),
    ("SS Warning", "SS Warning (e.g., WatchA4)", "str", True),
    ("SS Warning URL", "SS Warning URL", "str", True),
    ("Area", "Impact Area", "str", True)
]

def main():
    csv_file = "atlCSV.csv"
    backup_file = "atlCSV_backup.csv"
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Ensure you are in the correct directory.")
        return

    shutil.copy2(csv_file, backup_file)
    
    print("=========================================")
    print("      Storm Surge Data Entry Tool        ")
    print("=========================================")
    print(f"* Backup created as {backup_file}")
    print("* Press Ctrl+C at any time to cancel.")
    print("* Type 'CLEAR' on any edit prompt to erase its data.")
    print("-----------------------------------------\n")
    
    with open(csv_file, mode="r", encoding="utf-8") as read_file:
        reader = csv.DictReader(read_file)
        original_headers = reader.fieldnames
        rows = list(reader)

    # LOOP START
    while True:
        entry_type = input("\nAre you adding a [S]torm, [Y]ear spacer, [E]diting, or [Q]uit? (S/Y/E/Q): ").strip().upper()

        if entry_type == 'Q':
            break

        if entry_type == 'Y':
            y_val = prompt_field("Year (YYYY) for spacer", num_type="int", allow_blank=False)
            new_row = {
                "YYYY": y_val, "Storm": "", "Retire?": "", "Wikipedia": "", 
                "Date": "", "Cat": "", "Pres": "", "Dead": "", 
                "$bn": "", "minStmTide": "", "maxStmTide": "0", "TCR or Ref.": "", 
                "FEV": "", "Guidance": "", "SS Warning": "", "SS Warning URL": "", "Area": ""
            }
            rows.append(new_row)
            
        elif entry_type == 'E':
            edit_yr = prompt_field("Enter Year of storm to edit", num_type="int", allow_blank=False)
            edit_nm = prompt_field("Enter Storm Name", allow_blank=False).lower()
            
            target_row = next((r for r in rows if r['YYYY'] == edit_yr and r['Storm'].lower() == edit_nm), None)
            
            if not target_row:
                print(f"\n❌ Error: Could not find {edit_nm.title()} in {edit_yr}.")
                continue
                
            print("\n--- Editing (Press Enter to keep current value) ---")
            rows.remove(target_row) 
            
            new_row = {}
            for key, prompt, num_type, allow_blank in FIELD_DEFS:
                val = prompt_field(prompt, current_val=target_row.get(key, ""), num_type=num_type, allow_blank=allow_blank)
                
                if key == "Retire?":
                    val = val.title()
                    
                if key == "Area" and val and val.upper() != 'CLEAR':
                    while True:
                        proposed = format_area(val)
                        print(f"  -> Formatted Area: {proposed}")
                        choice = input("     Accept this? [Y]es, [N]o (try again), [M]anual override: ").strip().upper()
                        if choice == 'Y' or choice == '':
                            val = proposed
                            break
                        elif choice == 'M':
                            val = input("     Enter manual override exactly as desired: ").strip()
                            break
                        else:
                            val = input(f"     {prompt}: ").strip()
                            
                new_row[key] = val
            rows.append(new_row)
            
        elif entry_type == 'S':
            print("\nLeave a field blank and press Enter to skip.")
            new_row = {}
            for key, prompt, num_type, allow_blank in FIELD_DEFS:
                val = prompt_field(prompt, num_type=num_type, allow_blank=allow_blank)
                
                if key == "Retire?":
                    val = val.title()
                    
                if key == "Area" and val:
                    while True:
                        proposed = format_area(val)
                        print(f"  -> Formatted Area: {proposed}")
                        choice = input("     Accept this? [Y]es, [N]o (try again), [M]anual override: ").strip().upper()
                        if choice == 'Y' or choice == '':
                            val = proposed
                            break
                        elif choice == 'M':
                            val = input("     Enter manual override exactly as desired: ").strip()
                            break
                        else:
                            val = input(f"     {prompt}: ").strip()
                            
                new_row[key] = val
            rows.append(new_row)
            
        else:
            print("Invalid selection. Try again.")
            continue

        # Sort and Write immediately to preserve data
        clean_rows = []
        for r in rows:
            if any(str(v).strip() for v in r.values() if v is not None):
                clean_rows.append(r)

        def get_sort_key(row):
            year_str = str(row.get("YYYY", "")).strip()
            year = int(year_str) if year_str.isdigit() else -1
            storm_name = str(row.get("Storm", "")).strip().lower()
            
            if not storm_name:
                return (year, 13, 32, "") 
                
            date_str = str(row.get("Date", "")).lower()
            month_val = 0
            day_val = 0
            
            month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', date_str)
            if month_match:
                months = {
                    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
                }
                month_val = months[month_match.group(1)]
                day_val = 31 
                day_match = re.search(r'\d+', date_str)
                if day_match:
                    day_val = int(day_match.group())
                
            return (year, month_val, day_val, storm_name)

        clean_rows.sort(key=get_sort_key, reverse=True)

        for key in new_row.keys():
            if key not in original_headers:
                original_headers.append(key)

        with open(csv_file, mode="w", newline="", encoding="utf-8") as write_file:
            writer = csv.DictWriter(write_file, fieldnames=original_headers, extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            writer.writerows(clean_rows)
            
        identifier = new_row['YYYY'] if entry_type == 'Y' else f"{new_row.get('Storm', '').title()} ({new_row['YYYY']})"
        print(f"\n✅ Success: {identifier} saved to CSV.")
    
    # End of Loop - Trigger Markdown generation
    print("\n=========================================")
    print("Generating updated markdown table...")
    try:
        with open("README.md", "w", newline='\n') as readme_file:
            subprocess.run(["./generate_table.py"], stdout=readme_file, check=True)
        print("✅ Done! README.md has been updated.")
    except Exception as e:
        print(f"Error running generate_table.py: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🚫 Data entry cancelled by user. Program exited.")
        sys.exit(0)
