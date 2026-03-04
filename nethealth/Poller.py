import csv
import datetime
import time 
from typing import List, Tuple, Optional
from pythonping import ping
from pysnmp.hlapi import(
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, getCmd, nextCmd
)
import sqlite3 

snmpCommunity = "snmp_read"
sysname_oid = "1.3.6.1.2.1.1.5.0"
sysUpTime = "1.3.6.1.2.1.1.3.0"
hrProcessorLoad = "1.3.6.1.2.1.25.3.3.1.2"
hrStorageType = "1.3.6.1.2.1.25.2.3.1.2"
hrStorageRam = "1.3.6.1.2.1.25.2.1.2"
hrStorageUsed = "1.3.6.1.2.1.25.2.3.1.6"
hrStorageSize = "1.3.6.1.2.1.25.2.3.1.5"
hrStorageAllocationUnits = "1.3.6.1.2.1.25.2.3.1.4"
hrStorageDescr = "1.3.6.1.2.1.25.2.3.1.3"
hrStorageFixedDisk = "1.3.6.1.2.1.25.2.1.4"

#FUNCTIONS:
def snmp_get(ip: str, oid: str, port: int = 161, timeout: int = 3, retries: int = 2) -> str | None:
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(snmpCommunity, mpModel=1),  # SNMP v2c
        UdpTransportTarget((ip, port), timeout=timeout, retries=retries),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    # line 19 sends the packet, waits for a reply, unpacks the response
    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        print(f"SNMP error on {ip}: {errorIndication}")
        return None
    if errorStatus:
        print(f"SNMP error on {ip}: {errorStatus.prettyPrint()} at {errorIndex}")
        return None

    return str(varBinds[0][1])

def snmp_walk(ip: str, base_oid: str, port: int = 161, timeout: int = 3, retries: int = 2) -> Optional[List[Tuple[str, str]]]:
    results: List[Tuple[str, str]] = []

    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(snmpCommunity, mpModel=1),  # SNMP v2c
        UdpTransportTarget((ip, port), timeout=timeout, retries=retries),
        ContextData(),
        ObjectType(ObjectIdentity(base_oid)),
        lexicographicMode=False,   # stop when leaving base_oid
    )

    for (errorIndication, errorStatus, errorIndex, varBinds) in iterator:
        if errorIndication:
            print(f"SNMP WALK error on {ip}: {errorIndication}")
            return None
        if errorStatus:
            print(f"SNMP WALK error on {ip}: {errorStatus.prettyPrint()} at {errorIndex}")
            return None


        for oid_obj, val_obj in varBinds:
            results.append((oid_obj.prettyPrint(), str(val_obj)))

    return results

#Gets CPU load %
def cpuLoad(ip: str):
    rows = snmp_walk(ip, hrProcessorLoad)    
    loads = []
    if rows:
        for row in rows:
            oid = row[0]
            value = row[1]
            loads.append(int(value))
        if loads:
            cpu_avg = sum(loads) / len(loads)
            cpu_avg = round(cpu_avg, 2)
        print("CPU avg:", cpu_avg, "%")
        print("\n")
    return cpu_avg

#Gets RAM values (in GB and % used)
def ramSNMP(ip: str) -> Optional[Tuple[int, int]]:
            rows = snmp_walk(ip, hrStorageType)    
            if rows:
                for row in rows:
                    if row[1] == hrStorageRam:
                        ramIndex = row[0].split(".")[-1]
            if ramIndex:
                #Getting allocation units value to calculate RAM values into bytes
                ramAllocationUnits = snmp_get(ip, oid = hrStorageAllocationUnits + "." + ramIndex)

                #Getting total RAM
                ramSize = snmp_get(ip, oid = hrStorageSize + "." + ramIndex)
                ramSize = int(ramSize) * int(ramAllocationUnits)
                ramSizeMB = round(ramSize / (1024 ** 2), 2)
                ramSizeGB = round(ramSize / (1024 ** 3), 2)
                print("RAM Size: ", ramSizeMB, "MB" ," or" ,ramSizeGB ,"GB")

                #Getting total used RAM
                ramUsage = snmp_get(ip, oid = hrStorageUsed + "." + ramIndex)
                ramUsage = int(ramUsage) * int(ramAllocationUnits)
                ramUsageMB = round(ramUsage / (1024 ** 2), 2)
                ramUsageGB = round(ramUsage / (1024 ** 3), 2)
                print("RAM Usage: ", ramUsageMB, "MB" ," or" ,ramUsageGB ,"GB")
                
                #Getting RAM usage percent
                ramUsagePercent = ramUsageGB / ramSizeGB * 100
                ramUsagePercent = round(ramUsagePercent)
                print("Usage: ",ramUsagePercent, "%")
                print("\n")
            return ramUsagePercent, ramUsageGB, ramSizeGB

#Gets fixedDisk values (Storage in GB and % used)
def diskSNMP(ip: str) -> Optional[Tuple[int, int]]:
    rows = snmp_walk(ip, hrStorageType)
    if rows:
        for row in rows:
            if row[1] == hrStorageFixedDisk:
                diskIndex = row[0].split(".")[-1]
                fixedDiskAllocationUnits = snmp_get(ip, oid = hrStorageAllocationUnits + "." + diskIndex)
                storageDescr = snmp_get(ip, oid = hrStorageDescr + "." + diskIndex) 
                print("Disk: ",storageDescr)
                #Getting total size of each disk
                fixedDiskSize = snmp_get(ip, oid = hrStorageSize + "." + diskIndex)
                fixedDiskSize = int(fixedDiskSize) * int(fixedDiskAllocationUnits)
                fixedDiskMB = round(fixedDiskSize / (1024 ** 2), 2)
                fixedDiskGB = round(fixedDiskSize / (1024 ** 3), 2)
                print("Disk size: ", fixedDiskMB, "MB" ," or" , fixedDiskGB,"GB")

                #Getting used size of each disk
                fixedDiskUsage = snmp_get(ip, oid = hrStorageUsed + "." + diskIndex)
                fixedDiskUsage = int(fixedDiskUsage) * int(fixedDiskAllocationUnits)
                fixedDiskUsageMB = round(fixedDiskUsage / (1024 ** 2), 2)
                fixedDiskUsageGB = round(fixedDiskUsage / (1024 ** 3), 2)
                print("Disk used: ", fixedDiskUsageMB, "MB" ," or" , fixedDiskUsageGB,"GB")

                if fixedDiskGB > 1:
                    fixedDiskTotalGB = 0
                    fixedDiskTotalGB = fixedDiskTotalGB + fixedDiskGB
                    print("Total GB:", fixedDiskTotalGB)
                    fixedDiskTotalUsedGB = 0
                    fixedDiskTotalUsedGB = fixedDiskTotalUsedGB + fixedDiskUsageGB
                    fixedDiskUsagePercent = fixedDiskUsageGB / fixedDiskGB * 100
                    fixedDiskUsagePercent = round(fixedDiskUsagePercent, 2)
                    print("Used :", fixedDiskUsagePercent,"%")
                print("\n")
    return fixedDiskUsagePercent, fixedDiskTotalGB, fixedDiskTotalUsedGB


#Variable initialising:
latency = 0
cpu_avg = 0
ramIndex = None
diskIndex = None
upTime = None

#File path variables:
resultsDB = r"C:\Projects\Network_Health\nethealth\results.db"
csv_file = r"C:\Projects\Network_Health\nethealth\devices_simple.csv"

#sqlite connection
connection = sqlite3.connect(resultsDB)
dbCursor = connection.cursor()

#Main loop:

while True:
    with open(csv_file, "r") as csvfile:
        reader = csv.DictReader(csvfile, dialect="excel", delimiter=";", quotechar='"')
        for line in reader:
            ct = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("Timestamp:", ct)
            print("IP: ", line["IP"], "\n")
            response = ping(target=line["IP"], count=4, verbose=True, out_format=None)
            latency = response.rtt_avg_ms
            print(latency)
            print("\n")
            if latency < 1500:
                #Getting upTime
                upTime = snmp_get(
                    line["IP"],
                    oid = sysUpTime
                )
                if upTime != None:
                    upTimeSecondsTotal = int(upTime) / 100
                    upTimeSecondsTotal = round(upTimeSecondsTotal)
                    #upTimeSeconds = upTimeSecondsTotal % 60
                    #upTimeMinutesTotal = upTimeSecondsTotal // 60
                    #upTimeMinutes = upTimeMinutesTotal % 60
                    #upTimeHoursTotal = upTimeMinutesTotal // 60
                    #upTimeHours = upTimeHoursTotal % 60
                    #upTimeDays = upTimeHoursTotal // 24

                    #Getting hostname
                    host = snmp_get(line["IP"], oid=sysname_oid)
                    
                    #Getting CPU load %
                    cpu_avg = cpuLoad(line["IP"])

                    #Getting RAM data
                    ramUsagePercent, ramUsageGB, ramSizeGB = ramSNMP(line["IP"])

                    #Getting Hard Disk Data
                    fixedDiskUsagePercent, fixedDiskTotalGB, fixedDiskTotalUsedGB = diskSNMP(line["IP"])

                    #Add data to DB:
                    dbCursor.execute(
                        "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (ct, host, latency, cpu_avg, ramUsagePercent, fixedDiskUsagePercent, fixedDiskTotalGB, fixedDiskTotalUsedGB, ramSizeGB, ramUsageGB, upTimeSecondsTotal)
                    )
                    connection.commit()
                    print("\n")


                print("Waiting...")
                time.sleep(2.5)