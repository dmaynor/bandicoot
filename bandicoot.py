<td><a href="{{ url_for('view_log', log_id=log.id) }}">{{ log.id }}</a></td>
```

```python
@app.route("/log/<int:log_id>")
def view_log(log_id):
    """Show the full crash log from the database."""
    conn = get_db_connection()
    log = conn.execute("SELECT * FROM crash_logs WHERE id = ?", (log_id,)).fetchone()
    conn.close()
    
    if log is None:
        return "Log not found", 404

    return render_template("log.html", log=log)
```

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crash Log Details</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container mt-5">
    <h2>Crash Log #{{ log.id }}</h2>
    <p><strong>Crash Time:</strong> {{ log.crash_time }}</p>
    <p><strong>Process Name:</strong> {{ log.process_name }}</p>
    <p><strong>Exception Type:</strong> {{ log.exception_type }}</p>
    <p><strong>Termination Reason:</strong> {{ log.termination_reason }}</p>
    <p><strong>File Path:</strong> {{ log.file_path }}</p>
    <p><strong>Notation:</strong> {{ log.notation }}</p>
    <h3>Full Log Content</h3>
    <pre class="border p-3">{{ log.log_content }}</pre>
    <a href="{{ url_for('index') }}" class="btn btn-secondary">Back to Logs</a>
</body>
</html>