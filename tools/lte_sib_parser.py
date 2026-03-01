import csv

class LTE_SIB_Parser:
    def __init__(self, filename='lte_data.csv'):
        self.filename = filename

    def append_data(self, data):
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def parse(self, sib_data):
        # Assuming sib_data is a dictionary, we will convert it to a list for CSV
        row_data = [sib_data['param1'], sib_data['param2'], sib_data['param3']]
        self.append_data(row_data)
