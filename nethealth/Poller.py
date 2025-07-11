import csv
from pysnmp.hlapi.v3arch.asyncio import *
from pythonping import ping

i=0
cycleCount = 0
with open("devices.csv", newline="") as csvfile:
    spamreader = csv.reader(csvfile, dialect="excel", delimiter='|', quotechar=' ')
    reader = csv.DictReader(csvfile)
    for row in reader:
        cycleCount += 1
        print(" sop: "" ", row, "Number of cycles: ", cycleCount, "; and i: ", i)
        ping(target="10.0.0.10", verbose=True)
        
# last thing tried : to print row["IP"]. for some reason it doesnt work.