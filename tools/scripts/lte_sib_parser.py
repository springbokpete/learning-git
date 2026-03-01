#!/usr/bin/env python3
import re
import sys
import csv
import os
from datetime import datetime

OUTPUT_FILE = "sib_database.csv"

def decode_lte_eci(hex_value):
    eci = int(hex_value, 16)
    enodeb_id = eci >> 8
    cell_id = eci & 0xFF
    return eci, enodeb_id, cell_id

def main(file_path):

    # Ask user for channel number
    earfcn = input("Enter DL EARFCN (channel number): ").strip()

    if not earfcn.isdigit():
        print("Invalid EARFCN. Must be numeric.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # MCC
    mcc_match = re.search(r"mcc value\s*:\s*([\d,\s]+)", content)
    mcc = ''.join(mcc_match.group(1).replace(',', '').split()) if mcc_match else ""

    # MNC
    mnc_match = re.search(r"mnc value\s*:\s*([\d,\s]+)", content)
    mnc = ''.join(mnc_match.group(1).replace(',', '').split()) if mnc_match else ""

    # TAC
    tac_match = re.search(r"trackingAreaCode[\s\S]*?\(=\s*(\d+)\)", content)
    tac = tac_match.group(1) if tac_match else ""

    # Cell Identity
    cell_match = re.search(r"cellIdentity[\s\S]*?'([0-9A-Fa-f]+)'H", content)

    cell_hex = ""
    eci = ""
    enb = ""
    cell = ""

    if cell_match:
        cell_hex = cell_match.group(1)
        eci, enb, cell = decode_lte_eci(cell_hex)

    file_exists = os.path.isfile(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow([
                "Timestamp",
                "Source_File",
                "EARFCN_DL",
                "MCC",
                "MNC",
                "TAC",
                "Cell_Hex",
                "ECI_Decimal",
                "eNodeB_ID",
                "Cell_ID"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            os.path.basename(file_path),
            earfcn,
            mcc,
            mnc,
            tac,
            cell_hex,
            eci,
            enb,
            cell
        ])

    print(f"\nData appended to {OUTPUT_FILE}")

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python lte_sib_parser.py <sib_file.txt>")
        sys.exit(1)

    main(sys.argv[1])
