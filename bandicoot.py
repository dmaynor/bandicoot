#!/usr/bin/env python3

import os
import glob
import re
import sqlite3
import pandas as pd
import sys
import subprocess
import argparse
import getpass

# Default Bandicoot database directory
DEFAULT_DB_DIR = os.path.expanduser("~/.bandicoot")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "crash_logs.db")

# Log file extensions to scan
LOG_EXTENSIONS = ["crash", "diag", "ips", "shutdownStall"]
USER_CRASH_LOGS = [os.path.expanduser(f"~/Library/Logs/DiagnosticReports/*.{ext}") for ext in LOG_EXTENSIONS]
SYSTEM_CRASH_LOGS = [f"/Library/Logs/DiagnosticReports/*.{ext}" for ext in LOG_EXTENSIONS]

# SQL Statements
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS crash_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crash_time TEXT,
    process_name TEXT,
    exception_type TEXT,
    termination_reason TEXT,
    file_path TEXT UNIQUE,
    notation TEXT DEFAULT '',
    log_content TEXT
);
"""

INSERT_LOG_SQL = """
INSERT INTO crash_logs (crash_time, process_name, exception_type, termination_reason, file_path, log_content)
VALUES (?, ?, ?, ?, ?, ?);
"""

CHECK_EXISTING_SQL = """
SELECT file_path FROM crash_logs;
"""

COUNT_LOGS_SQL = """
SELECT COUNT(*) FROM crash_logs;
"""

def ensure_log_content_field(db_path):
    """Ensures that the log_content field exists in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(crash_logs);")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "log_content" not in columns:
        print("Adding 'log_content' field to crash_logs table...")
        cursor.execute("ALTER TABLE crash_logs ADD COLUMN log_content TEXT;")
        conn.commit()
    
    conn.close()

def ensure_notation_field(db_path):
    """Ensures that the notation field exists in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(crash_logs);")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "notation" not in columns:
        print("Adding 'notation' field to crash_logs table...")
        cursor.execute("ALTER TABLE crash_logs ADD COLUMN notation TEXT DEFAULT '';")
        conn.commit()
    
    conn.close()

def ask_user_first_run():
    """Prompts user if this is their first time running Bandicoot."""
    response = input("Bandicoot directory not found. Is this your first time running? (yes/no): ").strip().lower()
    return response in ["y", "yes"]

def wipe_database(db_path):
    """Deletes the existing database and reinitializes it."""
    db_dir = os.path.dirname(db_path)
    
    if os.path.exists(db_path):
        print(f"Wiping existing database at {db_path}...")
        os.remove(db_path)

    if os.path.exists(db_dir):
        print(f"Removing old Bandicoot directory: {db_dir}")
        os.rmdir(db_dir)  # Remove if empty

    # Proceed with fresh setup
    setup_bandicoot_directory(db_path)

def setup_bandicoot_directory(db_path):
    """Sets up the Bandicoot directory and database with proper ownership, avoiding dangerous locations."""
    db_dir = os.path.dirname(db_path)

    # Prevent creating the database in root or root's home directory
    if os.geteuid() == 0 or db_dir in ["/", "/root"]:
        response = input(f"⚠️ WARNING: You are about to create the database in {db_dir}. Are you sure? (yes/no): ").strip().lower()
        if response not in ["y", "yes"]:
            print("❌ Database creation aborted for safety.")
            sys.exit(1)

    if not os.path.exists(db_dir):
        if ask_user_first_run():
            print(f"Creating Bandicoot directory at {db_dir}...")
            os.makedirs(db_dir, exist_ok=True)
            os.chmod(db_dir, 0o700)  # Ensure only the user can access it
            print("✅ Directory created with correct permissions.")
        else:
            print("❌ Error: Please provide a Bandicoot database path with --db-path")
            sys.exit(1)
    
    if not os.path.exists(db_path):
        print(f"Creating Bandicoot database at {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_SQL)
        conn.commit()
        conn.close()
        os.chmod(db_path, 0o600)  # Restrict access to user only
        print("✅ Database initialized with correct permissions.")

    ensure_notation_field(db_path)
    ensure_log_content_field(db_path)

def check_permissions():
    """Checks if system crash logs are accessible; requests sudo if needed."""
    test_files = sum([glob.glob(path) for path in SYSTEM_CRASH_LOGS], [])
    
    if not test_files:
        print("No system crash logs found. Skipping permission check.")
        return True

    test_file = test_files[0]
    
    if os.access(test_file, os.R_OK):
        return True  # Has permission

    print(f"Permission denied for {test_file}. Requesting superuser access...")
    return False

def request_sudo():
    """Re-runs the script with sudo privileges if needed."""
    if os.geteuid() != 0:
        print("Re-running with superuser privileges...")
        subprocess.call(["sudo", sys.executable] + sys.argv)
        sys.exit()

def parse_crash_log(file_path, verbose=False):
    """
    Extracts key details and stores the full log content.
    If verbose is True, prints each line before parsing it.
    Safeguards against 'no such group' errors by checking the number of groups first.
    """

    try:
        with open(file_path, "r", errors="ignore") as f:
            log_content = f.read()
        
        crash_time = None
        process_name = None
        exception_type = None
        termination_reason = None

        for line in log_content.splitlines():
            if verbose:
                print(f"Parsing line: {line.strip()}")

            if not crash_time:
                match = re.search(r"(Date/Time|Timestamp|Time):\s+(.+)", line)
                if match:
                    crash_time = match.group(2)

            if not process_name:
                match = re.search(r"(Process|Executable|Application):\s+(.+)", line)
                if match:
                    process_name = match.group(2)

            if not exception_type:
                match = re.search(r"(Exception Type|Fault Type|Error Type):\s+(.+)", line)
                if match:
                    exception_type = match.group(2)

            if not termination_reason:
                match = re.search(r"(Termination Reason|Cause|Reason):\s+(.+)", line)
                if match:
                    termination_reason = match.group(2)

        return {
            "crash_time": crash_time if crash_time else "Unknown",
            "process_name": process_name if process_name else "Unknown",
            "exception_type": exception_type if exception_type else "Unknown",
            "termination_reason": termination_reason if termination_reason else "Unknown",
            "file_path": file_path,
            "log_content": log_content
        }

    except Exception as e:
        return {
            "crash_time": "Error",
            "process_name": "Error",
            "exception_type": str(e),
            "termination_reason": "Error",
            "file_path": file_path,
            "log_content": "Error loading log"
        }

def store_crash_logs(db_path, logs):
    """Stores crash logs in SQLite, avoiding duplicates."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(CREATE_TABLE_SQL)
    cursor.execute(CHECK_EXISTING_SQL)
    existing_files = {row[0] for row in cursor.fetchall()}
    
    new_logs = []
    
    for log in logs:
        if log["file_path"] not in existing_files:
            cursor.execute(
                INSERT_LOG_SQL,
                (
                    log["crash_time"],
                    log["process_name"],
                    log["exception_type"],
                    log.get("termination_reason", "Unknown"),
                    log["file_path"],
                    log["log_content"]
                )
            )
            new_logs.append(log)

    conn.commit()
    cursor.execute(COUNT_LOGS_SQL)
    total_logs = cursor.fetchone()[0]

    conn.close()
    return total_logs, new_logs

def main():
    """Main function to parse crash logs and store them in SQLite."""
    parser = argparse.ArgumentParser(description="Bandicoot - macOS Crash Log Analyzer")
    parser.add_argument("--db-path", type=str, help="Path to the Bandicoot SQLite database")
    parser.add_argument("--wipe", action="store_true", help="Wipe the existing database and start fresh")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode for detailed parsing output")

    args = parser.parse_args()
    db_path = args.db_path if args.db_path else DEFAULT_DB_PATH

    if args.wipe:
        wipe_database(db_path)

    setup_bandicoot_directory(db_path)

    if not check_permissions():
        request_sudo()

    all_logs = sum([glob.glob(path) for path in USER_CRASH_LOGS + SYSTEM_CRASH_LOGS], [])

    parsed_logs = [parse_crash_log(log, verbose=args.verbose) for log in all_logs]

    total_logs, new_logs = store_crash_logs(db_path, parsed_logs)

    print(f"Total crash logs in database: {total_logs}")
    if new_logs:
        print(f"New crash logs added ({len(new_logs)}):")
        for log in new_logs:
            print(f"- {log['crash_time']} | {log['process_name']} | {log['exception_type']}")

if __name__ == "__main__":
    main()