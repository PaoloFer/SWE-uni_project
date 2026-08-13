from utils.csv_utils import CsvManager



def test():
    manager = CsvManager("./data/patient.csv", delimiter=";", has_header=False)

    print(manager.read())