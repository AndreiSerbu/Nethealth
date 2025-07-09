import csv
from pythonping import ping
with open("devices.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        print(row)

