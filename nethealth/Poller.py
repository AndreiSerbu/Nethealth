import csv
import datetime
from pythonping import ping
import sqlite3

ct = datetime.datetime.now()

with open("devices.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile, dialect="excel", delimiter=";", quotechar='"')
    for line in reader:
        print(" Value: "" ", line["IP"])
        #ping(target=line["IP"], verbose=True)



connection = sqlite3.connect("results.db")
dbCursor = connection.cursor()
#dbCursor = dbCursor.execute("CREATE TABLE results(timestamp, host, latency_ms, up_down)")
dbCursor.execute(
    "INSERT INTO results VALUES (?, ?, ?, ?)",
            (ct, "test", "test", "test")
)
connection.commit()
res = dbCursor.execute("SELECT timestamp FROM results")
res.fetchone()

