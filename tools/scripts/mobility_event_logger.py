import re
import pandas as pd

RRC_FILE = "event.txt"
CSV_FILE = "127_handover_Measurement_events.csv"


def parse_rrc_config(text):
    results = {}

    # -------- A3 --------
    if "eventA3" in text:
        offset_match = re.search(r"a3-Offset\s+:\s+\d+\s+\(=\s+([-\d\.]+)\s+dB\)", text)
        hyst_match = re.search(r"hysteresis\s+:\s+\d+\s+\(=\s+([-\d\.]+)\s+dB\)", text)
        ttt_match = re.search(r"timeToTrigger\s+:\s+ms(\d+)", text)

        results["A3"] = {
            "offset": float(offset_match.group(1)) if offset_match else None,
            "threshold": None,
            "hysteresis": float(hyst_match.group(1)) if hyst_match else None,
            "ttt": int(ttt_match.group(1)) if ttt_match else None
        }

    # -------- A2 --------
    if "eventA2" in text:
        thresh_match = re.search(r"threshold-RSRP\s+:\s+\d+\s+\(=\s+([-\d\.]+)\s+dBm\)", text)
        hyst_match = re.search(r"hysteresis\s+:\s+\d+\s+\(=\s+([-\d\.]+)\s+dB\)", text)
        ttt_match = re.search(r"timeToTrigger\s+:\s+ms(\d+)", text)

        results["A2"] = {
            "offset": None,
            "threshold": float(thresh_match.group(1)) if thresh_match else None,
            "hysteresis": float(hyst_match.group(1)) if hyst_match else None,
            "ttt": int(ttt_match.group(1)) if ttt_match else None
        }

    # -------- A5 --------
    if "eventA5" in text:
        thresh_match = re.search(r"threshold-RSRP\s+:\s+\d+\s+\(=\s+([-\d\.]+)\s+dBm\)", text)
        hyst_match = re.search(r"hysteresis\s+:\s+\d+\s+\(=\s+([-\d\.]+)\s+dB\)", text)
        ttt_match = re.search(r"timeToTrigger\s+:\s+ms(\d+)", text)

        results["A5"] = {
            "offset": None,
            "threshold": float(thresh_match.group(1)) if thresh_match else None,
            "hysteresis": float(hyst_match.group(1)) if hyst_match else None,
            "ttt": int(ttt_match.group(1)) if ttt_match else None
        }

    # -------- A6 --------
    if "eventA6" in text or "eventA6-r10" in text:
        offset_match = re.search(r"a6-Offset.*\s:\s+\d+\s+\(=\s+([-\d\.]+)\s+dB\)", text)
        hyst_match = re.search(r"hysteresis\s+:\s+\d+\s+\(=\s+([-\d\.]+)\s+dB\)", text)
        ttt_match = re.search(r"timeToTrigger\s+:\s+ms(\d+)", text)

        results["A6"] = {
            "offset": float(offset_match.group(1)) if offset_match else None,
            "threshold": None,
            "hysteresis": float(hyst_match.group(1)) if hyst_match else None,
            "ttt": int(ttt_match.group(1)) if ttt_match else None
        }

    return results


def update_csv(event_configs):
    df = pd.read_csv(CSV_FILE)

    # Ensure numeric safety
    df["Current Cell ID"] = df["Current Cell ID"].fillna(0).astype(int)

    # ---- TRANSLATE LTE ECI ----
    df["System.1"] = df["Current Cell ID"] // 256
    df["BTS Cell ID"] = df["Current Cell ID"] % 256

    updated_rows = 0

    for event_name, config in event_configs.items():

        mask = df["Measurement Event"].astype(str).str.strip() == f"Event {event_name}"

        if mask.any():
            df.loc[mask, "Configured Offset (dB)"] = config["offset"]
            df.loc[mask, "Configured Threshold (dBm)"] = config["threshold"]
            df.loc[mask, "Configured Hysteresis (dB)"] = config["hysteresis"]
            df.loc[mask, "Configured TTT (ms)"] = config["ttt"]

            updated_rows += mask.sum()

    df.to_csv(CSV_FILE, index=False)

    print(f"\nUpdated {updated_rows} rows.")
    print("Translated ALL Current Cell IDs into eNodeB + BTS Cell ID.")


def main():
    print("\nParsing RRC configuration...\n")

    with open(RRC_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    events = parse_rrc_config(text)

    if not events:
        print("No supported events detected.")
        return

    print("Events detected:")
    for e in events:
        print(f" - {e}")

    update_csv(events)

    print("Process complete.")


if __name__ == "__main__":
    main()
