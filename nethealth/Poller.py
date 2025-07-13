import csv
from pythonping import ping

with open("devices.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile, dialect="excel", delimiter=";", quotechar='"')
    for line in reader:
        cycleCount += 1
        print(" Value: "" ", line["IP"])
        ping(target=line["IP"], verbose=True)