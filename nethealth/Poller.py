import csv
from pythonping import ping 
with open("devices.csv", newline="") as csvfile:
    spamreader = csv.reader(csvfile, delimiter='|', quotechar=' ')
    reader = csv.DictReader(csvfile)
    for row in reader:
        print(row)
