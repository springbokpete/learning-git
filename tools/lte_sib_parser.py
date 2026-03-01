import re

# Corrections made to regex patterns for SIB1 file format

# Pattern to capture Mobile Country Code (MCC)
mcc_pattern = r'([0-9]{3})'

# Pattern to capture Mobile Network Code (MNC)
mnc_pattern = r'([0-9]{2,3})'

# Pattern to capture Tracking Area Code (TAC)
# This captures both hex and decimal formats
# Hex: 0x[0-9A-Fa-f]{1,6}, Decimal: [0-9]{1,6}
tac_pattern = r'(0x[0-9A-Fa-f]{1,6}|[0-9]{1,6})'

# Pattern to capture Cell Identity
cell_id_pattern = r'(0x[0-9A-Fa-f]{1,6}|[0-9]{1,6})'

# Sample data and test
input_data = '''MCC: 123, MNC: 45, TAC: 0x003C, Cell Identity: 0x1E240\nMCC: 456, MNC: 12, TAC: 12345, Cell Identity: 987654'''  

# Function to extract values based on the regex patterns
def extract_values(data):
    mcc_matches = re.findall(mcc_pattern, data)
    mnc_matches = re.findall(mnc_pattern, data)
    tac_matches = re.findall(tac_pattern, data)
    cell_id_matches = re.findall(cell_id_pattern, data)
    return mcc_matches, mnc_matches, tac_matches, cell_id_matches

# Uncomment the line below to test the extraction
# print(extract_values(input_data))