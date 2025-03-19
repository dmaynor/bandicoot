# **Bandicoot - macOS Crash Log Analyzer**

## **Overview**
Bandicoot is a **macOS crash log analysis tool** that:
- **Scans system and user crash logs** (`.crash`, `.diag`, `.ips`, `.shutdownStall`).
- **Extracts key details** (process name, exception type, termination reason).
- **Stores logs in an SQLite database**.
- **Provides a web-based interface** for viewing and annotating logs.

## **Features**
- 📄 **Parses & stores full crash logs** from `~/Library/Logs/DiagnosticReports/`
- 📝 **Allows adding notations** to logs for tracking.
- 🌐 **Web-based UI** to browse and update logs.
- 🔗 **Click on log IDs** to view the full log content.

---

## **Installation**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-repo/bandicoot.git
cd bandicoot
```

### **2️⃣ Set Up Virtual Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

---

## **Usage**
### **Running the Log Parser**
```bash
python bandicoot.py
```
- By default, logs are stored in `~/.bandicoot/crash_logs.db`
- **Options:**
  - `--wipe` → Reset the database before running.
  - `--verbose` → Debug log parsing.

### **Running the Web App**
```bash
cd bandicoot_web
python app.py
```
- Open your browser: **`http://127.0.0.1:5000`**
- Click on **log IDs** to view full crash logs.

---

## **Example Workflow**
1. **Run `bandicoot.py`** to collect logs:
   ```bash
   python bandicoot.py --wipe
   ```
2. **Start the web app**:
   ```bash
   cd bandicoot_web
   python app.py
   ```
3. **View logs in the browser**:
   - Go to **`http://127.0.0.1:5000`**.
   - Click on **log IDs** to view details.
   - Add **notations** to logs.

---

## **Contributing**
Feel free to open **issues** or **pull requests** if you have improvements!

---

## **License**
📜 MIT License

---

🚀 **Now you're ready to analyze crash logs effortlessly!** 🚀
