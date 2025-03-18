#!/usr/bin/env python3

import os
import glob
import re
import sqlite3
import pandas as pd

# Paths to crash logs
USER_CRASH_LOGS = os.path.expanduser("~/Library/Logs/DiagnosticReports/*.crash")
SYSTEM_CRASH_LOGS = "/Library/Logs/DiagnosticReports/*.crash"

# Database file
DB_PATH = os.path.expanduser("~/crash_logs.db")

# SQL Statements
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS crash_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crash_time TEXT,
    process_name TEXT,
    exception_type TEXT,
    termination_reason TEXT,
    file_path TEXT UNIQUE
);
"""

INSERT_LOG_SQL = """
INSERT INTO crash_logs (crash_time, process_name, exception_type, termination_reason, file_path)
VALUES (?, ?, ?, ?, ?);
"""

CHECK_EXISTING_SQL = """
SELECT file_path FROM crash_logs;
"""

COUNT_LOGS_SQL = """
SELECT COUNT(*) FROM crash_logs;
"""

# Function to extract key crash details
def parse_crash_log(file_path):
    try:
        with open(file_path, "r", errors="ignore") as f:
            log_content = f.read()
        
        # Extract key fields
        crash_time = re.search(r"Date/Time:\s+(.+)", log_content)
        process_name = re.search(r"Process:\s+(\S+)", log_content)
        exception_type = re.search(r"Exception Type:\s+(.+)", log_content)
        termination_reason = re.search(r"Termination Reason:\s+(.+)", log_content)

        return {
            "crash_time": crash_time.group(1) if crash_time else "Unknown",
            "process_name": process_name.group(1) if process_name else "Unknown",
            "exception_type": exception_type.group(1) if exception_type else "Unknown",
            "termination_reason": termination_reason.group(1) if termination_reason else "Unknown",
            "file_path": file_path
        }
    
    except Exception as e:
        return {
            "crash_time": "Error",
            "process_name": "Error",
            "exception_type": str(e),
            "termination_reason": "Error",
            "file_path": file_path
        }

# Function to check and insert logs into SQLite
def store_crash_logs(logs):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute(CREATE_TABLE_SQL)

    # Fetch existing logs to avoid duplicates
    cursor.execute(CHECK_EXISTING_SQL)
    existing_files = {row[0] for row in cursor.fetchall()}
    
    new_logs = []
    
    for log in logs:
        if log["file_path"] not in existing_files:
            cursor.execute(INSERT_LOG_SQL, (log["crash_time"], log["process_name"], log["exception_type"], log["termination_reason"], log["file_path"]))
            new_logs.append(log)

    # Commit and close
    conn.commit()

    # Get total logs in the database
    cursor.execute(COUNT_LOGS_SQL)
    total_logs = cursor.fetchone()[0]

    conn.close()
    return total_logs, new_logs

# Collect all crash logs
all_logs = glob.glob(USER_CRASH_LOGS) + glob.glob(SYSTEM_CRASH_LOGS)

# Parse logs
parsed_logs = [parse_crash_log(log) for log in all_logs]

# Store logs in database and check for new ones
total_logs, new_logs = store_crash_logs(parsed_logs)

# Print summary
print(f"Total crash logs in database: {total_logs}")
if new_logs:
    print(f"New crash logs added ({len(new_logs)}):")
    for log in new_logs:
        print(f"- {log['crash_time']} | {log['process_name']} | {log['exception_type']}")

# Convert new logs to DataFrame and display
df = pd.DataFrame(new_logs)
if not df.empty:
    import ace_tools as tools
    tools.display_dataframe_to_user(name="New Crash Logs", dataframe=df)