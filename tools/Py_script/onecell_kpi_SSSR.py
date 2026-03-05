import tarfile
import webbrowser
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# ================== CHANGE ONLY THIS ==================
root_data_folder = Path("~/projects/learning-git/tools/MK").expanduser()
target_mac = "0005B9571F3B"
session_setup_target_pct = 99
connection_drop_max_pct = 1
# =====================================================

output_html = Path(__file__).with_name(f"ONECELL_SSSR_{target_mac}_2weeks.html")
auto_open_output = True

print(f"🔍 Searching in root: {root_data_folder}")
print(f"   Looking for MAC: {target_mac}\n")

all_dfs = []
processed_tgz = 0
txt_fallback = 0

# First try: .tgz files (compressed)
for tgz_path in root_data_folder.rglob("*.tgz"):
    if target_mac.upper() not in str(tgz_path).upper():
        continue
    print(f"  📦 Found .tgz: {tgz_path.name}")
    processed_tgz += 1
    try:
        with tarfile.open(tgz_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.lower().endswith(".txt") and "performancelog" in member.name.lower():
                    file_obj = tar.extractfile(member)
                    df = pd.read_csv(file_obj, sep=",", header=0, low_memory=False, encoding="utf-8")
                    all_dfs.append(df)
                    print("     ✓ Extracted txt from inside tgz")
    except Exception as e:
        print(f"     ⚠️ Error opening tgz: {e}")

# Fallback: if no tgz worked, look for already extracted .txt files
if len(all_dfs) == 0:
    print("\nNo .tgz data found → trying extracted .txt files...")
    for txt_path in root_data_folder.rglob("*.txt"):
        if target_mac.upper() not in str(txt_path).upper():
            continue
        print(f"  📄 Found extracted txt: {txt_path.name}")
        txt_fallback += 1
        try:
            df = pd.read_csv(txt_path, sep=",", header=0, low_memory=False, encoding="utf-8")
            all_dfs.append(df)
        except Exception as e:
            print(f"     ⚠️ Error reading txt: {e}")

if not all_dfs:
    print(f"\n❌ Still no data found for MAC {target_mac}")
    print("   → Make sure root_data_folder points to the folder that contains the data folders")
    exit()

big_df = pd.concat(all_dfs, ignore_index=True)
print(f"\n✅ Loaded {len(big_df):,} rows from {processed_tgz} tgz + {txt_fallback} txt files")

print("\n📋 Columns in your files:")
print(list(big_df.columns))
print("-" * 80)


def normalize_col_name(value):
    return "".join(ch.lower() for ch in str(value) if ch.isalnum())


normalized_to_original_col = {
    normalize_col_name(col): col for col in big_df.columns
}


def pick_col(*candidates):
    for candidate in candidates:
        found = normalized_to_original_col.get(normalize_col_name(candidate))
        if found:
            return found
    return None


ue_lost_col = pick_col("UeContextRelReqRadioConnectionWithUeLost")
ue_rel_sum_col = pick_col("UeContextRelReqSum")

rrc_succ_col = pick_col("RRCCONNESTABSUCCSUM", "RrcConnEstabSuccSum")
rrc_att_col = pick_col("RRCCONNESTABATTSUM", "RrcConnEstabAttSum")
erab_init_succ_sum_col = pick_col("ERABESTABINITSUCCNBRQCISUM", "ErabEstabInitSuccNbrQciSum")
erab_init_att_sum_col = pick_col("ERABESTABINITATTNBRQCISUM", "ErabEstabInitAttNbrQciSum")
s1_succ_col = pick_col("S1SIGCONNESTABSUCCESS", "S1SigConnEstabSuccess", "S1SIGCONNESTABSUCC")
s1_att_col = pick_col("S1SIGCONNESTABATTEMTED", "S1sigConnEstabAttemted", "S1SIGCONNESTABATTEMPTED", "S1SIGCONNESTABATT")

qci1_init_succ_col = pick_col("ERABESTABINITSUCCNBRQCI1")
qci1_add_succ_col = pick_col("ERABESTABADDSUCCNBRQCI1")
qci1_init_att_col = pick_col("ERABESTABINITATTNBRQCI1")
qci1_add_att_col = pick_col("ERABESTABADDATTNBRQCI1")

if ue_lost_col and ue_rel_sum_col:
    print(f"✅ Drop-rate columns mapped: {ue_lost_col} / {ue_rel_sum_col}")
else:
    print("⚠️ Drop-rate KPI columns not found with expected names.")

big_df["datetime"] = pd.to_datetime(
    big_df["date"] + " " + big_df["time"],
    format="%Y/%m/%d %H:%M:%S",
    errors="coerce",
)
big_df = big_df.dropna(subset=["datetime"]).sort_values("datetime")

for col in big_df.columns:
    if any(k in col.upper() for k in ["RRCCONNESTABATT", "RRCCONNESTABSUCC", "ERABESTABINITATT", "ERABESTABINITSUCC", "S1SIGCONNESTAB", "NETWORKENTRY"]):
        big_df[col] = pd.to_numeric(big_df[col], errors="coerce").fillna(0)

required_kpi_cols = [
    ue_lost_col,
    ue_rel_sum_col,
    rrc_succ_col,
    rrc_att_col,
    erab_init_succ_sum_col,
    erab_init_att_sum_col,
    s1_succ_col,
    s1_att_col,
    qci1_init_succ_col,
    qci1_add_succ_col,
    qci1_init_att_col,
    qci1_add_att_col,
]

for col in [column for column in required_kpi_cols if column]:
    big_df[col] = pd.to_numeric(big_df[col], errors="coerce").fillna(0)


def make_increment_delta_column(source_col):
    if not source_col:
        return None
    delta_col = f"{source_col}__DELTA"
    delta = big_df[source_col].diff()
    big_df[delta_col] = delta.where(delta >= 0, big_df[source_col]).fillna(0)
    return delta_col


qci1_init_succ_delta_col = make_increment_delta_column(qci1_init_succ_col)
qci1_add_succ_delta_col = make_increment_delta_column(qci1_add_succ_col)
qci1_init_att_delta_col = make_increment_delta_column(qci1_init_att_col)
qci1_add_att_delta_col = make_increment_delta_column(qci1_add_att_col)

agg_dict = {col: "sum" for col in big_df.columns if any(k in col.upper() for k in ["ATT", "SUCC", "SUM"])}
agg_dict.update({col: "mean" for col in big_df.columns if "PERC" in col.upper()})

counter_behavior = {
    "CELLAVAILABLETIME": "resets",
    "CQIMEANCW1": "increments",
    "CQIMEANCW2": "resets",
    "DRBIPLATEDLQCI1": "resets",
    "DRBIPLATEDLQCI8": "resets",
    "DRBIPTHPDLQCISUM": "resets",
    "DRBIPTHPULQCISUM": "resets",
    "DRBPDCPSDUAIRLOSSRATEDLQCI1": "resets",
    "DRBPDCPSDULOSSRATEULQCI1": "resets",
    "DRBPDCPSDUBITRATEDLQCISUM": "resets",
    "DRBUEACTIVEDLQCI1": "resets",
    "DRBUEACTIVEDLQCISUM": "resets",
    "DRBUEACTIVEULQCI1": "resets",
    "DRBUEACTIVEULQCISUM": "resets",
    "ERABESTABADDATTNBRQCI1": "resets",
    "ERABESTABADDSUCCNBRQCI1": "increments",
    "ERABESTABINITATTNBRQCISUM": "increments",
    "ERABESTABINITATTNBRQCI1": "increments",
    "ERABESTABINITATTNBRQCI5": "increments",
    "ERABESTABINITSUCCNBRQCISUM": "increments",
    "ERABESTABINITSUCCNBRQCI1": "increments",
    "ERABESTABINITSUCCNBRQCI5": "increments",
    "ERABESTABINCHOSUCCNBRQCI1": "increments",
    "ERABRELACTNBRQCISUM": "increments",
    "ERABRELACTNBRQCI1": "increments",
    "ERABRELACTNBRQCI5": "increments",
    "HOINTRAFREQOUTATTSUM": "increments",
    "HOINTRAFREQOUTSUCCSUM": "increments",
    "HOINTERFREQMEASGAPOUTATT": "increments",
    "HOINTERFREQMEASGAPOUTSUCC": "increments",
    "HOINTERFREQNOMEASGAPOUTATT": "increments",
    "HOINTERFREQNOMEASGAPOUTSUCC": "increments",
    "HOINTRAENBOUTATTSUM": "increments",
    "HOINTRAENBOUTSUCCSUM": "increments",
    "MACDATABYTESDLSUM": "resets",
    "MACDATABYTESULSUM": "resets",
    "NUMCSFBFROMCONN": "resets",
    "NUMCSFBFROMIDLE": "increments",
    "NUMCSFBIND": "increments",
    "NUMECSFBIND": "increments",
    "RRCCONNESTABATTSUM": "increments",
    "RRCCONNESTABSUCCSUM": "increments",
    "RRUPRBTOTDL": "increments",
    "RRUPRBTOTUL": "resets",
    "VOLTEAUDIOLONGGAPDL": "resets",
    "VOLTEAUDIOLONGGAPUL": "resets",
    "VOLTEAUDIOSHORTGAPDL": "resets",
    "VOLTEAUDIOSHORTGAPUL": "resets",
}

for col in big_df.columns:
    behavior = counter_behavior.get(col.upper())
    if behavior == "increments":
        agg_dict[col] = "sum"
    elif behavior == "resets":
        agg_dict[col] = "max"

if ue_lost_col:
    agg_dict[ue_lost_col] = "sum"
if ue_rel_sum_col:
    agg_dict[ue_rel_sum_col] = "sum"

for delta_col in [qci1_init_succ_delta_col, qci1_add_succ_delta_col, qci1_init_att_delta_col, qci1_add_att_delta_col]:
    if delta_col:
        agg_dict[delta_col] = "sum"

hourly = big_df.groupby(pd.Grouper(key="datetime", freq="h")).agg(agg_dict).reset_index()

if "RRCCONNESTABSUCCSUM" in hourly.columns and "RRCCONNESTABATTSUM" in hourly.columns:
    hourly["RRC_SSR_%"] = (hourly["RRCCONNESTABSUCCSUM"] / hourly["RRCCONNESTABATTSUM"] * 100).where(hourly["RRCCONNESTABATTSUM"] > 0)
if "ERABESTABINITSUCCNBRQCISUM" in hourly.columns and "ERABESTABINITATTNBRQCISUM" in hourly.columns:
    hourly["ERAB_SSR_%"] = (hourly["ERABESTABINITSUCCNBRQCISUM"] / hourly["ERABESTABINITATTNBRQCISUM"] * 100).where(hourly["ERABESTABINITATTNBRQCISUM"] > 0)
if "RRC_SSR_%" in hourly.columns and "ERAB_SSR_%" in hourly.columns:
    hourly["Session_Setup_Success_Rate_%"] = hourly["RRC_SSR_%"] * hourly["ERAB_SSR_%"] / 100

if all(col in hourly.columns for col in [rrc_succ_col, rrc_att_col, erab_init_succ_sum_col, erab_init_att_sum_col, s1_succ_col, s1_att_col]):
    hourly["ERAB_Accessibility_%"] = (
        (hourly[rrc_succ_col] / hourly[rrc_att_col])
        * (hourly[erab_init_succ_sum_col] / hourly[erab_init_att_sum_col])
        * (hourly[s1_succ_col] / hourly[s1_att_col])
        * 100
    ).where((hourly[rrc_att_col] > 0) & (hourly[erab_init_att_sum_col] > 0) & (hourly[s1_att_col] > 0))

if all(col in hourly.columns for col in [qci1_init_succ_delta_col, qci1_add_succ_delta_col, qci1_init_att_delta_col, qci1_add_att_delta_col]):
    qci1_numerator = hourly[qci1_init_succ_delta_col] + hourly[qci1_add_succ_delta_col]
    qci1_denominator = hourly[qci1_init_att_delta_col] + hourly[qci1_add_att_delta_col]
    hourly["ERAB_Setup_Success_Ratio_QCI1_%"] = ((qci1_numerator / qci1_denominator * 100).where(qci1_denominator > 0).clip(lower=0, upper=100))

if ue_lost_col in hourly.columns and ue_rel_sum_col in hourly.columns:
    hourly["Connection_Drop_Rate_%"] = (hourly[ue_lost_col] / hourly[ue_rel_sum_col] * 100).where(hourly[ue_rel_sum_col] > 0)


def format_pct(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def make_status_class(value, threshold, mode):
    if pd.isna(value) or threshold is None:
        return "neutral"
    if mode == "min":
        return "good" if value >= threshold else "bad"
    if mode == "max":
        return "good" if value <= threshold else "bad"
    return "neutral"


def build_graph_html(frame, series_key, title, trace_name, threshold=None, threshold_label=None, threshold_color=None):
    graph_fig = go.Figure()
    graph_fig.add_trace(
        go.Scatter(
            x=frame["datetime"],
            y=frame[series_key],
            mode="lines+markers",
            name=trace_name,
        )
    )
    if threshold is not None:
        graph_fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color=threshold_color,
            annotation_text=threshold_label,
        )

    graph_fig.update_xaxes(title_text="Datetime")
    graph_fig.update_yaxes(title_text="Percent (%)")
    graph_fig.update_layout(
        title=title,
        height=420,
        hovermode="x unified",
        template="plotly_dark",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return pio.to_html(
        graph_fig,
        include_plotlyjs=False,
        full_html=False,
        config={"displaylogo": False, "responsive": True},
    )


kpi_definitions = [
    {
        "key": "Session_Setup_Success_Rate_%",
        "label": "Session Setup Success Rate",
        "threshold": session_setup_target_pct,
        "mode": "min",
        "target_label": f"Target ≥ {session_setup_target_pct}%",
    },
    {
        "key": "Connection_Drop_Rate_%",
        "label": "Connection Drop Rate",
        "threshold": connection_drop_max_pct,
        "mode": "max",
        "target_label": f"Max ≤ {connection_drop_max_pct}%",
    },
    {
        "key": "ERAB_Accessibility_%",
        "label": "E-RAB Accessibility",
        "threshold": None,
        "mode": "none",
        "target_label": "No fixed threshold",
    },
    {
        "key": "ERAB_Setup_Success_Ratio_QCI1_%",
        "label": "E-RAB Setup Success Ratio, QCI1",
        "threshold": None,
        "mode": "none",
        "target_label": "No fixed threshold",
    },
]

graph_definitions = [
    {
        "key": "Session_Setup_Success_Rate_%",
        "title": f"Session Setup Success Rate - MAC {target_mac}",
        "trace_name": "Session Setup Success Rate (%)",
        "threshold": session_setup_target_pct,
        "threshold_label": f"Target {session_setup_target_pct}%",
        "threshold_color": "green",
    },
    {
        "key": "Connection_Drop_Rate_%",
        "title": f"Connection Drop Rate - MAC {target_mac}",
        "trace_name": "Connection Drop Rate (%)",
        "threshold": connection_drop_max_pct,
        "threshold_label": f"Max {connection_drop_max_pct}%",
        "threshold_color": "red",
    },
    {
        "key": "ERAB_Accessibility_%",
        "title": f"E-RAB Accessibility - MAC {target_mac}",
        "trace_name": "E-RAB Accessibility (%)",
    },
    {
        "key": "ERAB_Setup_Success_Ratio_QCI1_%",
        "title": f"E-RAB Setup Success Ratio, QCI 1 - MAC {target_mac}",
        "trace_name": "E-RAB Setup Success Ratio, QCI 1 (%)",
    },
]

latest_row = hourly.iloc[-1] if not hourly.empty else pd.Series(dtype=float)
kpi_cards_html = ""

for definition in kpi_definitions:
    value = latest_row.get(definition["key"], float("nan"))
    status_class = make_status_class(value, definition["threshold"], definition["mode"])
    status_text = {"good": "On target", "bad": "Needs attention", "neutral": "Informational"}[status_class]

    kpi_cards_html += f"""
    <div class=\"kpi-card {status_class}\">
        <div class=\"kpi-title\">{definition['label']}</div>
        <div class=\"kpi-value\">{format_pct(value)}</div>
        <div class=\"kpi-meta\">{definition['target_label']}</div>
        <div class=\"kpi-status\">{status_text}</div>
    </div>
    """

graph_panels_html = ""
panel_index = 0

for graph in graph_definitions:
    if graph["key"] not in hourly.columns:
        continue

    panel_index += 1
    panel_id = f"graph-panel-{panel_index}"
    graph_html = build_graph_html(
        frame=hourly,
        series_key=graph["key"],
        title=graph["title"],
        trace_name=graph["trace_name"],
        threshold=graph.get("threshold"),
        threshold_label=graph.get("threshold_label"),
        threshold_color=graph.get("threshold_color"),
    )

    graph_panels_html += f"""
    <div class=\"graph-block\">
        <button class=\"toggle-btn\" onclick=\"toggleGraph('{panel_id}', this)\">Hide {graph['trace_name']}</button>
        <div id=\"{panel_id}\" class=\"graph-panel\">{graph_html}</div>
    </div>
    """

if panel_index == 0:
    graph_panels_html = "<p>No KPI graph columns available.</p>"

table_columns = [
    "datetime",
    "Session_Setup_Success_Rate_%",
    "Connection_Drop_Rate_%",
    "ERAB_Accessibility_%",
    "ERAB_Setup_Success_Ratio_QCI1_%",
]
available_table_columns = [col for col in table_columns if col in hourly.columns]

if available_table_columns:
    recent_table = hourly[available_table_columns].tail(48).copy()
    if "datetime" in recent_table.columns:
        recent_table["datetime"] = recent_table["datetime"].dt.strftime("%Y-%m-%d %H:%M")
    for col in recent_table.columns:
        if col != "datetime":
            recent_table[col] = recent_table[col].map(lambda value: "" if pd.isna(value) else f"{value:.2f}")
    recent_table_html = recent_table.to_html(index=False, classes="recent-table", border=0)
else:
    recent_table_html = "<p>No KPI columns available for recent table.</p>"

dashboard_html = f"""
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>ONECELL KPI Dashboard - {target_mac}</title>
    <script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
    <style>
        :root {{
            --bg: #0f172a;
            --panel: #111827;
            --panel-2: #1f2937;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --good: #14532d;
            --good-border: #22c55e;
            --bad: #7f1d1d;
            --bad-border: #ef4444;
            --neutral: #1e3a8a;
            --neutral-border: #60a5fa;
        }}
        body {{
            margin: 0;
            font-family: Segoe UI, Arial, sans-serif;
            background: linear-gradient(180deg, var(--bg), #020617);
            color: var(--text);
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: var(--panel);
            border: 1px solid #374151;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
        }}
        .title {{
            margin: 0 0 6px;
            font-size: 24px;
            font-weight: 700;
        }}
        .subtitle {{
            color: var(--muted);
            margin: 0;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }}
        .kpi-card {{
            border-radius: 12px;
            padding: 14px;
            border: 1px solid #374151;
            background: var(--panel);
        }}
        .kpi-card.good {{ background: var(--good); border-color: var(--good-border); }}
        .kpi-card.bad {{ background: var(--bad); border-color: var(--bad-border); }}
        .kpi-card.neutral {{ background: var(--neutral); border-color: var(--neutral-border); }}
        .kpi-title {{ font-size: 14px; color: #d1d5db; }}
        .kpi-value {{ font-size: 30px; font-weight: 700; margin: 6px 0; }}
        .kpi-meta {{ font-size: 12px; color: #cbd5e1; }}
        .kpi-status {{ margin-top: 8px; font-weight: 600; font-size: 12px; }}
        .panel {{
            background: var(--panel);
            border: 1px solid #374151;
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 16px;
        }}
        .graph-block {{
            background: #0b1224;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 10px;
            margin-bottom: 12px;
        }}
        .toggle-btn {{
            background: #1f2937;
            color: var(--text);
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 10px;
        }}
        .toggle-btn:hover {{
            background: #334155;
        }}
        .graph-panel.hidden {{
            display: none;
        }}
        h2 {{ margin: 4px 0 12px; font-size: 18px; }}
        .recent-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .recent-table th, .recent-table td {{ padding: 8px; border-bottom: 1px solid #374151; text-align: left; }}
        .recent-table th {{ background: var(--panel-2); }}
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <h1 class=\"title\">ONECELL KPI Dashboard</h1>
            <p class=\"subtitle\">MAC: {target_mac} | Time range: {hourly['datetime'].min()} → {hourly['datetime'].max()}</p>
        </div>

        <div class=\"kpi-grid\">{kpi_cards_html}</div>

        <div class=\"panel\">
            <h2>KPI Graphs (toggle each)</h2>
            {graph_panels_html}
        </div>

        <div class=\"panel\">
            <h2>Recent KPI Samples (last 48 hours)</h2>
            {recent_table_html}
        </div>
    </div>
    <script>
        function toggleGraph(panelId, button) {{
            const panel = document.getElementById(panelId);
            panel.classList.toggle('hidden');
            const isHidden = panel.classList.contains('hidden');
            const buttonLabel = button.textContent.replace(/^Hide\s|^Show\s/, '');
            button.textContent = (isHidden ? 'Show ' : 'Hide ') + buttonLabel;
        }}
    </script>
</body>
</html>
"""

with open(output_html, "w", encoding="utf-8") as file:
    file.write(dashboard_html)

print(f"\n🎉 Dashboard saved → {output_html}")
print(f"   Full path: {output_html.resolve()}")
print(f"   Time range: {hourly['datetime'].min()} → {hourly['datetime'].max()}")

if auto_open_output:
    try:
        webbrowser.open(output_html.resolve().as_uri())
        print("🌐 Opened dashboard in your default browser")
    except Exception as e:
        print(f"⚠️ Could not auto-open browser: {e}")

print("✅ Done")
