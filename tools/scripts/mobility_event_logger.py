#!/usr/bin/env python3
import pandas as pd
import re
import os

event_list_file = "Event_List.csv"
rrc_file = "event.txt"
output_file = "Mobility_Report.csv"

# -------------------------------
# Load Event_List.csv
# -------------------------------
try:
    df = pd.read_csv(event_list_file)
except FileNotFoundError:
    print("Event_List.csv not found.")
    exit()

print("\nFirst 20 rows:\n")
print(df.head(20)[["Time", "HOA type", "Current LTE PCI", "Current Cell ID", "Handover status"]])

selection = input("\nEnter the row number to analyse: ").strip()

if not selection.isdigit():
    print("Invalid input.")
    exit()

selection = int(selection)

if selection < 0 or selection >= len(df):
    print("Row out of range.")
    exit()

row = df.loc[selection]

# -------------------------------
# Cell ID → eNodeB + Sector
# -------------------------------
cell_id = int(row["Current Cell ID"])
enb_id = cell_id // 256
sector_id = cell_id % 256

# -------------------------------
# Extract RRC config
# -------------------------------
try:
    with open(rrc_file, "r", encoding="utf-8") as f:
        rrc_text = f.read()
except FileNotFoundError:
    print("event.txt not found.")
    exit()

event_type_match = re.search(r"event(A\d|B\d)", rrc_text, re.I)
event_type = event_type_match.group(0).upper() if event_type_match else "Unknown"

offset_match = re.search(r"\(=\s*([\d\.]+)\s*dB\)", rrc_text)
offset = float(offset_match.group(1)) if offset_match else None

hyst_match = re.search(r"hysteresis\s*:\s*\d+\s*\(=\s*([\d\.]+)\s*dB\)", rrc_text, re.I)
hysteresis = float(hyst_match.group(1)) if hyst_match else None

ttt_match = re.search(r"timeToTrigger\s*:\s*ms(\d+)", rrc_text, re.I)
ttt = int(ttt_match.group(1)) if ttt_match else None

# -------------------------------
# Build report row
# -------------------------------
report_data = {
    "Time": row["Time"],
    "HOA Type": row["HOA type"],
    "Serving PCI": row["Current LTE PCI"],
    "Cell ID": cell_id,
    "eNodeB ID": enb_id,
    "Sector ID": sector_id,
    "Handover Status": row["Handover status"],
    "Handover Delay (s)": row["Handover delay (s)"],
    "Event Trigger Type": event_type,
    "Offset (dB)": offset,
    "Hysteresis (dB)": hysteresis,
    "TTT (ms)": ttt,
    "Longitude": row["Lon."],
    "Latitude": row["Lat."]
}

report_df = pd.DataFrame([report_data])

# -------------------------------
# Append to file instead of overwrite
# -------------------------------
if os.path.exists(output_file):
    report_df.to_csv(output_file, mode='a', header=False, index=False)
else:
    report_df.to_csv(output_file, index=False)

print("\nRow added to Mobility_Report.csv successfully.")
