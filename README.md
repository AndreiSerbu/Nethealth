# NetHealth — SNMP Network Monitor

A lightweight, headless network monitoring tool that polls devices via SNMP and ICMP, collecting key health metrics and storing them in a local SQLite database.

Built as a learning project to understand SNMP, HOST-RESOURCES-MIB, and Python-based infrastructure tooling.

---

## What it monitors

- **Ping / Latency** — ICMP round-trip time in ms
- **Hostname** — via `sysName` OID
- **CPU Usage** — average load across all cores via `hrProcessorLoad`
- **RAM** — total GB, used GB, and usage percentage via `hrStorageTable`
- **Disk** — total and used GB across fixed disks (partitions > 1GB) via `hrStorageTable`
- **Uptime** — seconds since last reboot via `sysUpTime`

All data is timestamped and written to a SQLite database for later retrieval and display.

---

## Requirements

- Python 3.10+
- SNMP v2c enabled on target devices (community string: configurable)
- Target devices must have `HOST-RESOURCES-MIB` available (standard on Linux/Windows with net-snmp or Windows SNMP service)

Install dependencies:

```bash
pip install pysnmp pythonping
```

> Note: `pythonping` requires elevated privileges (run as Administrator on Windows, or with `sudo` on Linux)

---

## Configuration

Edit the following variables at the top of the script:

```python
snmpCommunity = "snmp_read"       # Your SNMP community string
resultsDB = r"path\to\results.db" # SQLite database path
csv_file = r"path\to\devices.csv" # Device list path
```

**Device list format** (`devices.csv`):

```
IP;Hostname
CW-01;192.168.11.15;Windows;Windows Client
CL-01;192.168.11.30;Debian;Debian Client
```

---

## Database schema

Data is stored in a single `results` table:

| Column | Description |
|---|---|
| timestamp | Poll time (YYYY-MM-DD HH:MM:SS) |
| host | Device hostname |
| latency_ms | Ping RTT in milliseconds |
| CPU Usage | Average CPU load % |
| RAM Usage | RAM usage % |
| Hard Disk Usage | Disk usage % (largest disk) |
| Hard Disk Total GB | Total fixed disk capacity in GB |
| Hard Disk Used GB | Used disk space in GB |
| RAM Total GB | Total physical RAM in GB |
| RAM Used GB | Used RAM in GB |
| uptime | Seconds since last reboot |

---

## Usage

```bash
python nethealth.py
```

Runs indefinitely, polling all devices in the CSV on each loop. Stop with `Ctrl+C`.

Devices that don't respond to ping (latency > 1500ms) or fail SNMP are skipped for that poll cycle.

---

## Project structure

```
nethealth/
├── poller.py       # Main poller
├── devices_simple.csv
└── results.db         
