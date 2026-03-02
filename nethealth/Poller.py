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
hrProcessorLoad = "1.3.6.1.2.1.25.3.3.1.2"
hrStorageType = "1.3.6.1.2.1.25.2.3.1.2"
hrStorageRam = "1.3.6.1.2.1.25.2.1.2"
hrStorageUsed = "1.3.6.1.2.1.25.2.3.1.6"
hrStorageSize = "1.3.6.1.2.1.25.2.3.1.5"
hrStorageAllocationUnits = "1.3.6.1.2.1.25.2.3.1.4"
hrStorageDescr = "1.3.6.1.2.1.25.2.3.1.3"
hrStorageFixedDisk = "1.3.6.1.2.1.25.2.1.4"

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

latency = 0
cpu_avg = 0
fixedDiskTotalGB = 0
fixedDiskTotalUsedGB = 0

#File path variables:
resultsDB = r"C:\Projects\Network_Health\nethealth\results.db"
csv_file = r"C:\Projects\Network_Health\nethealth\devices_simple.csv"

#Main loop:
main = 1

with open(csv_file, "r") as csvfile:
    reader = csv.DictReader(csvfile, dialect="excel", delimiter=";", quotechar='"')
    for line in reader:
        ct = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("Time:", ct)
        print("IP: ", line["IP"])
        response = ping(target=line["IP"], count=4, verbose=True, out_format=None)
        latency = response.rtt_avg_ms
        
        #Getting hostname
        host = snmp_get(
            line["IP"],
            oid=sysname_oid
        )

        #Getting CPU load %
        rows = snmp_walk(line["IP"], hrProcessorLoad)    
        loads = []
        if rows:
            for row in rows:
                oid = row[0]
                value = row[1]
                loads.append(int(value))
            if loads:
                cpu_avg = sum(loads) / len(loads)
            print("CPU avg:", cpu_avg, "%")
        
        #Getting ramIndex from hrStorageType
        rows = snmp_walk(line["IP"], hrStorageType)    
        if rows:
            for row in rows:
                if row[1] == hrStorageRam:
                    ramIndex = row[0].split(".")[-1]
        
        #Getting allocation units value to calculate RAM values into bytes
        ramAllocationUnits = snmp_get(line["IP"], oid = hrStorageAllocationUnits + "." + ramIndex)

        #Getting total RAM
        ramSize = snmp_get(line["IP"], oid = hrStorageSize + "." + ramIndex)
        ramSize = int(ramSize) * int(ramAllocationUnits)
        ramSizeMB = round(ramSize / (1024 ** 2), 2)
        ramSizeGB = round(ramSize / (1024 ** 3), 2)
        print("RAM Size: ", ramSizeMB, "MB" ," or" ,ramSizeGB ,"GB")

        #Getting total used RAM
        ramUsage = snmp_get(line["IP"], oid = hrStorageUsed + "." + ramIndex)
        ramUsage = int(ramUsage) * int(ramAllocationUnits)
        ramUsageMB = round(ramUsage / (1024 ** 2), 2)
        ramUsageGB = round(ramUsage / (1024 ** 3), 2)
        print("RAM Usage: ", ramUsageMB, "MB" ," or" ,ramUsageGB ,"GB")
        
        #Getting RAM usage percent
        ramUsagePercent = ramUsageGB / ramSizeGB * 100
        ramUsagePercent = round(ramUsagePercent)
        print(ramUsagePercent, "%")

        #hrStorageFixedDisk
        rows = snmp_walk(line["IP"], hrStorageType)    
        if rows:
            for row in rows:
                if row[1] == hrStorageFixedDisk:
                    diskIndex = row[0].split(".")[-1]
                    
                    fixedDiskAllocationUnits = snmp_get(line["IP"], oid = hrStorageAllocationUnits + "." + diskIndex)
                    
                    storageDescr = snmp_get(line["IP"], oid = hrStorageDescr + "." + diskIndex) 
                    print(storageDescr)

                    #Getting total size of each disk
                    fixedDiskSize = snmp_get(line["IP"], oid = hrStorageSize + "." + diskIndex)
                    fixedDiskSize = int(fixedDiskSize) * int(fixedDiskAllocationUnits)
                    fixedDiskMB = round(fixedDiskSize / (1024 ** 2), 2)
                    fixedDiskGB = round(fixedDiskSize / (1024 ** 3), 2)
                    print("Disk size: ", fixedDiskMB, "MB" ," or" , fixedDiskGB,"GB")

                    #Getting used size of each disk
                    fixedDiskUsage = snmp_get(line["IP"], oid = hrStorageUsed + "." + diskIndex)
                    fixedDiskUsage = int(fixedDiskUsage) * int(fixedDiskAllocationUnits)
                    fixedDiskUsageMB = round(fixedDiskUsage / (1024 ** 2), 2)
                    fixedDiskUsageGB = round(fixedDiskUsage / (1024 ** 3), 2)
                    print("Disk used: ", fixedDiskUsageMB, "MB" ," or" , fixedDiskUsageGB,"GB")

                    if fixedDiskGB > 1:
                        fixedDiskTotalGB = fixedDiskTotalGB + fixedDiskGB
                        print(fixedDiskTotalGB)
                        fixedDiskTotalUsedGB = fixedDiskTotalUsedGB + fixedDiskUsageGB
                        fixedDiskUsagePercent = fixedDiskUsageGB / fixedDiskGB * 100
                        fixedDiskUsagePercent = round(fixedDiskUsagePercent, 2)
                        print(fixedDiskUsagePercent)
                    

        #Add data to DB:
        connection = sqlite3.connect(resultsDB)
        dbCursor = connection.cursor()
        dbCursor.execute(
            "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ct, host, latency, "test", cpu_avg, ramUsagePercent, fixedDiskUsagePercent, fixedDiskTotalGB, fixedDiskTotalUsedGB)
        )
        connection.commit()
        print("\n")


        print("Waiting...")
        time.sleep(2.5)