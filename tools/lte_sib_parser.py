#!/usr/bin/env python3
import re
import sys

def decode_lte_eci(hex_value):
    eci = int(hex_value, 16)
    enodeb_id = eci >> 8
    cell_id = eci & 0xFF
    return eci, enodeb_id, cell_id

def main(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # MCC
    mcc_match = re.search(r"mcc value\s*:\s*([\d,\s]+)", content)
    mcc = ''.join(mcc_match.group(1).replace(',', '').split()) if mcc_match else None

    # MNC
    mnc_match = re.search(r"mnc value\s*:\s*([\d,\s]+)", content)
    mnc = ''.join(mnc_match.group(1).replace(',', '').split()) if mnc_match else None

    # TAC (decimal inside brackets)
    tac_match = re.search(r"trackingAreaCode[\s\S]*?\(=\s*(\d+)\)", content)
    tac = tac_match.group(1) if tac_match else None

    # Cell Identity (hex + decimal)
    cell_match = re.search(r"cellIdentity[\s\S]*?'([0-9A-Fa-f]+)'H\s*\(=\s*(\d+)\)", content)

    print("\n========== LTE SIB1 DECODE ==========\n")

    if mcc:
        print(f"MCC: {mcc}")
    if mnc:
        print(f"MNC: {mnc}")
    if tac:
        print(f"TAC: {tac}")

    if cell_match:
        cell_hex = cell_match.group(1)
        eci, enb, cell = decode_lte_eci(cell_hex)

        print(f"\nCell Identity (Hex): {cell_hex}")
        print(f"ECI (Decimal): {eci}")
        print(f"eNodeB ID: {enb}")
        print(f"Cell ID: {cell}")

    print("\n=====================================\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lte_sib_parser.py <sib_file.txt>")
        sys.exit(1)

    main(sys.argv[1])
