import csv
import datetime
from pythonping import ping
import sqlite3
#dbCursor = dbCursor.execute("CREATE TABLE results(timestamp, host, latency_ms, up_down)")
latency = 0
with open("devices.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile, dialect="excel", delimiter=";", quotechar='"')
    for line in reader:
        ct = datetime.datetime.now()
        print("Time:", ct)
        print("IP: ", line["IP"])
        response = ping(target=line["IP"], count=4, verbose=True, out_format=None)
        latency = response.rtt_avg_ms
        host = line["Hostname"]
        connection = sqlite3.connect("results.db")
        dbCursor = connection.cursor()
        dbCursor.execute(
            "INSERT INTO results VALUES (?, ?, ?, ?)",
                (ct, host, latency, "test")
        )
        connection.commit()
        print("\n")