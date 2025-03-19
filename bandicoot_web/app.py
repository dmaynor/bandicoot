#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

# Path to Bandicoot database
DB_PATH = os.path.expanduser("~/.bandicoot/crash_logs.db")

app = Flask(__name__)

def get_db_connection():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    """Display crash logs."""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM crash_logs").fetchall()
    conn.close()
    return render_template("index.html", logs=logs)

@app.route("/update", methods=["POST"])
def update():
    """Update notation field in the database."""
    log_id = request.form.get("log_id")
    notation = request.form.get("notation")

    if log_id:
        conn = get_db_connection()
        conn.execute("UPDATE crash_logs SET notation = ? WHERE id = ?", (notation, log_id))
        conn.commit()
        conn.close()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
