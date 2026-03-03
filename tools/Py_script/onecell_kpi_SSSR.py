import tarfile
import pandas as pd
from pathlib import Path
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# ================== CHANGE ONLY THIS ==================
root_data_folder = Path("~/projects/learning-git/tools/MK").expanduser()
target_mac = "0005B9571F3B"
session_setup_target_pct = 99
connection_drop_max_pct = 1
# =====================================================

output_html = f"ONECELL_SSSR_{target_mac}_2weeks.html"

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
                    f = tar.extractfile(member)
                    df = pd.read_csv(f, sep=",", header=0, low_memory=False, encoding="utf-8")
                    all_dfs.append(df)
                    print(f"     ✓ Extracted txt from inside tgz")
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
    print("   → Make sure root_data_folder points to the folder that contains the '2026-02-19' folder")
    print("   → Example: C:\\Users\\PieterBakker\\Documents\\ONECELL\\KPI DATA Sample")
    exit()

big_df = pd.concat(all_dfs, ignore_index=True)
print(f"\n✅ Loaded {len(big_df):,} rows from {processed_tgz} tgz + {txt_fallback} txt files")

# Show columns from first file (very useful)
print("\n📋 Columns in your files:")
print(list(big_df.columns))
print("-" * 80)

def normalize_col_name(value):
    return ''.join(ch.lower() for ch in str(value) if ch.isalnum())

normalized_to_original_col = {
    normalize_col_name(col): col for col in big_df.columns
}

def pick_col(*candidates):
    for candidate in candidates:
        found = normalized_to_original_col.get(normalize_col_name(candidate))
        if found:
            return found
    return None

ue_lost_col = pick_col('UeContextRelReqRadioConnectionWithUeLost')
ue_rel_sum_col = pick_col('UeContextRelReqSum')

rrc_succ_col = pick_col('RRCCONNESTABSUCCSUM', 'RrcConnEstabSuccSum')
rrc_att_col = pick_col('RRCCONNESTABATTSUM', 'RrcConnEstabAttSum')
erab_init_succ_sum_col = pick_col('ERABESTABINITSUCCNBRQCISUM', 'ErabEstabInitSuccNbrQciSum')
erab_init_att_sum_col = pick_col('ERABESTABINITATTNBRQCISUM', 'ErabEstabInitAttNbrQciSum')
s1_succ_col = pick_col('S1SIGCONNESTABSUCCESS', 'S1SigConnEstabSuccess', 'S1SIGCONNESTABSUCC')
s1_att_col = pick_col('S1SIGCONNESTABATTEMTED', 'S1sigConnEstabAttemted', 'S1SIGCONNESTABATTEMPTED', 'S1SIGCONNESTABATT')

qci1_init_succ_col = pick_col('ERABESTABINITSUCCNBRQCI1')
qci1_add_succ_col = pick_col('ERABESTABADDSUCCNBRQCI1')
qci1_init_att_col = pick_col('ERABESTABINITATTNBRQCI1')
qci1_add_att_col = pick_col('ERABESTABADDATTNBRQCI1')

qci1_init_succ_delta_col = None
qci1_add_succ_delta_col = None
qci1_init_att_delta_col = None
qci1_add_att_delta_col = None

if ue_lost_col and ue_rel_sum_col:
    print(f"✅ Drop-rate columns mapped: {ue_lost_col} / {ue_rel_sum_col}")
else:
    print("⚠️ Drop-rate KPI columns not found with expected names.")
    print("   Expected something like: UeContextRelReqRadioConnectionWithUeLost and UeContextRelReqSum")

# Parse datetime
big_df['datetime'] = pd.to_datetime(
    big_df['date'] + ' ' + big_df['time'],
    format='%Y/%m/%d %H:%M:%S',
    errors='coerce'
)
big_df = big_df.dropna(subset=['datetime']).sort_values('datetime')

# Numeric conversion (only columns that exist)
for col in big_df.columns:
    if any(k in col.upper() for k in ['RRCCONNESTABATT', 'RRCCONNESTABSUCC', 'ERABESTABINITATT', 
                                      'ERABESTABINITSUCC', 'S1SIGCONNESTAB', 'NETWORKENTRY']):
        big_df[col] = pd.to_numeric(big_df[col], errors='coerce').fillna(0)

required_kpi_cols = [
    ue_lost_col, ue_rel_sum_col,
    rrc_succ_col, rrc_att_col,
    erab_init_succ_sum_col, erab_init_att_sum_col,
    s1_succ_col, s1_att_col,
    qci1_init_succ_col, qci1_add_succ_col,
    qci1_init_att_col, qci1_add_att_col
]

for col in [column for column in required_kpi_cols if column]:
    big_df[col] = pd.to_numeric(big_df[col], errors='coerce').fillna(0)

# For increment counters used in QCI1 KPI, use non-negative deltas per sample before hourly aggregation.
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

# Hourly aggregation
agg_dict = {col: 'sum' for col in big_df.columns if any(k in col.upper() for k in ['ATT', 'SUCC', 'SUM'])}
agg_dict.update({col: 'mean' for col in big_df.columns if 'PERC' in col.upper()})

counter_behavior = {
    'CELLAVAILABLETIME': 'resets',
    'CQIMEANCW1': 'increments',
    'CQIMEANCW2': 'resets',
    'DRBIPLATEDLQCI1': 'resets',
    'DRBIPLATEDLQCI8': 'resets',
    'DRBIPTHPDLQCISUM': 'resets',
    'DRBIPTHPULQCISUM': 'resets',
    'DRBPDCPSDUAIRLOSSRATEDLQCI1': 'resets',
    'DRBPDCPSDULOSSRATEULQCI1': 'resets',
    'DRBPDCPSDUBITRATEDLQCISUM': 'resets',
    'DRBUEACTIVEDLQCI1': 'resets',
    'DRBUEACTIVEDLQCISUM': 'resets',
    'DRBUEACTIVEULQCI1': 'resets',
    'DRBUEACTIVEULQCISUM': 'resets',
    'ERABESTABADDATTNBRQCI1': 'resets',
    'ERABESTABADDSUCCNBRQCI1': 'increments',
    'ERABESTABINITATTNBRQCISUM': 'increments',
    'ERABESTABINITATTNBRQCI1': 'increments',
    'ERABESTABINITATTNBRQCI5': 'increments',
    'ERABESTABINITSUCCNBRQCISUM': 'increments',
    'ERABESTABINITSUCCNBRQCI1': 'increments',
    'ERABESTABINITSUCCNBRQCI5': 'increments',
    'ERABESTABINCHOSUCCNBRQCI1': 'increments',
    'ERABRELACTNBRQCISUM': 'increments',
    'ERABRELACTNBRQCI1': 'increments',
    'ERABRELACTNBRQCI5': 'increments',
    'HOINTRAFREQOUTATTSUM': 'increments',
    'HOINTRAFREQOUTSUCCSUM': 'increments',
    'HOINTERFREQMEASGAPOUTATT': 'increments',
    'HOINTERFREQMEASGAPOUTSUCC': 'increments',
    'HOINTERFREQNOMEASGAPOUTATT': 'increments',
    'HOINTERFREQNOMEASGAPOUTSUCC': 'increments',
    'HOINTRAENBOUTATTSUM': 'increments',
    'HOINTRAENBOUTSUCCSUM': 'increments',
    'MACDATABYTESDLSUM': 'resets',
    'MACDATABYTESULSUM': 'resets',
    'NUMCSFBFROMCONN': 'resets',
    'NUMCSFBFROMIDLE': 'increments',
    'NUMCSFBIND': 'increments',
    'NUMECSFBIND': 'increments',
    'RRCCONNESTABATTSUM': 'increments',
    'RRCCONNESTABSUCCSUM': 'increments',
    'RRUPRBTOTDL': 'increments',
    'RRUPRBTOTUL': 'resets',
    'VOLTEAUDIOLONGGAPDL': 'resets',
    'VOLTEAUDIOLONGGAPUL': 'resets',
    'VOLTEAUDIOSHORTGAPDL': 'resets',
    'VOLTEAUDIOSHORTGAPUL': 'resets'
}

for col in big_df.columns:
    behavior = counter_behavior.get(col.upper())
    if behavior == 'increments':
        agg_dict[col] = 'sum'
    elif behavior == 'resets':
        agg_dict[col] = 'max'

# Ensure these two fields are also aggregated for Connection Drop Rate
if ue_lost_col:
    agg_dict[ue_lost_col] = 'sum'
if ue_rel_sum_col:
    agg_dict[ue_rel_sum_col] = 'sum'

# Ensure QCI1 increment-delta fields are summed per hour.
for delta_col in [qci1_init_succ_delta_col, qci1_add_succ_delta_col, qci1_init_att_delta_col, qci1_add_att_delta_col]:
    if delta_col:
        agg_dict[delta_col] = 'sum'

hourly = big_df.groupby(pd.Grouper(key='datetime', freq='h')).agg(agg_dict).reset_index()

# Build KPI
if 'RRCCONNESTABSUCCSUM' in hourly.columns and 'RRCCONNESTABATTSUM' in hourly.columns:
    hourly['RRC_SSR_%'] = (hourly['RRCCONNESTABSUCCSUM'] / hourly['RRCCONNESTABATTSUM'] * 100).where(hourly['RRCCONNESTABATTSUM'] > 0)
if 'ERABESTABINITSUCCNBRQCISUM' in hourly.columns and 'ERABESTABINITATTNBRQCISUM' in hourly.columns:
    hourly['ERAB_SSR_%'] = (hourly['ERABESTABINITSUCCNBRQCISUM'] / hourly['ERABESTABINITATTNBRQCISUM'] * 100).where(hourly['ERABESTABINITATTNBRQCISUM'] > 0)

if 'RRC_SSR_%' in hourly.columns and 'ERAB_SSR_%' in hourly.columns:
    hourly['Session_Setup_Success_Rate_%'] = hourly['RRC_SSR_%'] * hourly['ERAB_SSR_%'] / 100

if all(col in hourly.columns for col in [rrc_succ_col, rrc_att_col, erab_init_succ_sum_col, erab_init_att_sum_col, s1_succ_col, s1_att_col]):
    hourly['ERAB_Accessibility_%'] = (
        (hourly[rrc_succ_col] / hourly[rrc_att_col])
        * (hourly[erab_init_succ_sum_col] / hourly[erab_init_att_sum_col])
        * (hourly[s1_succ_col] / hourly[s1_att_col])
        * 100
    ).where(
        (hourly[rrc_att_col] > 0)
        & (hourly[erab_init_att_sum_col] > 0)
        & (hourly[s1_att_col] > 0)
    )

if all(col in hourly.columns for col in [qci1_init_succ_delta_col, qci1_add_succ_delta_col, qci1_init_att_delta_col, qci1_add_att_delta_col]):
    qci1_numerator = hourly[qci1_init_succ_delta_col] + hourly[qci1_add_succ_delta_col]
    qci1_denominator = hourly[qci1_init_att_delta_col] + hourly[qci1_add_att_delta_col]
    hourly['ERAB_Setup_Success_Ratio_QCI1_%'] = (
        (qci1_numerator / qci1_denominator * 100)
        .where(qci1_denominator > 0)
        .clip(lower=0, upper=100)
    )

if ue_lost_col in hourly.columns and ue_rel_sum_col in hourly.columns:
    hourly['Connection_Drop_Rate_%'] = (
        hourly[ue_lost_col] / hourly[ue_rel_sum_col] * 100
    ).where(hourly[ue_rel_sum_col] > 0)

# Plot 2x2 KPI charts (new KPIs below existing top row)
fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        f'Session Setup Success Rate - MAC {target_mac}',
        f'Connection Drop Rate - MAC {target_mac}',
        f'E-RAB Accessibility - MAC {target_mac}',
        f'E-RAB Setup Success Ratio, QCI 1 - MAC {target_mac}'
    )
)

if 'Session_Setup_Success_Rate_%' in hourly.columns:
    fig.add_trace(
        go.Scatter(
            x=hourly['datetime'],
            y=hourly['Session_Setup_Success_Rate_%'],
            mode='lines+markers',
            name='Session Setup Success Rate (%)'
        ),
        row=1, col=1
    )
    fig.add_hline(
        y=session_setup_target_pct,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Target {session_setup_target_pct}%",
        row=1, col=1
    )

if 'Connection_Drop_Rate_%' in hourly.columns:
    fig.add_trace(
        go.Scatter(
            x=hourly['datetime'],
            y=hourly['Connection_Drop_Rate_%'],
            mode='lines+markers',
            name='Connection Drop Rate (%)'
        ),
        row=1, col=2
    )
    fig.add_hline(
        y=connection_drop_max_pct,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Max {connection_drop_max_pct}%",
        row=1, col=2
    )

if 'ERAB_Accessibility_%' in hourly.columns:
    fig.add_trace(
        go.Scatter(
            x=hourly['datetime'],
            y=hourly['ERAB_Accessibility_%'],
            mode='lines+markers',
            name='E-RAB Accessibility (%)'
        ),
        row=2, col=1
    )

if 'ERAB_Setup_Success_Ratio_QCI1_%' in hourly.columns:
    fig.add_trace(
        go.Scatter(
            x=hourly['datetime'],
            y=hourly['ERAB_Setup_Success_Ratio_QCI1_%'],
            mode='lines+markers',
            name='E-RAB Setup Success Ratio, QCI 1 (%)'
        ),
        row=2, col=2
    )

for subplot_row in [1, 2]:
    for subplot_col in [1, 2]:
        fig.update_xaxes(title_text='Datetime', row=subplot_row, col=subplot_col)
        fig.update_yaxes(title_text='Percent (%)', row=subplot_row, col=subplot_col)

fig.update_layout(height=1000, hovermode="x unified")
fig.show()

fig.write_html(output_html)
print(f"\n🎉 Chart saved → {output_html}")
print(f"   Time range: {hourly['datetime'].min()} → {hourly['datetime'].max()}")

