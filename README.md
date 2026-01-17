# 📂 Python Download Automator

A lightweight Python script that monitors your **Downloads** folder and automatically organizes files into categories (Images, Docs, Installers, etc.) based on their file extensions.

## ⚙️ Main Components

### 1. The Extension Dictionary (`EXTENSION_MAP`)
This is the "brain" of the sorting logic. It maps specific folder names to a list of file extensions.
* **Key:** The name of the folder where files will go (e.g., `"Images"`).
* **Value:** A list of extensions that belong to that category (e.g., `[".jpg", ".png"]`).
* **Customization:** You can easily add new rules here. For example, to sort Photoshop files, you would add `"Design": [".psd", ".ai"]`.

***Extension Dictionary***
  ```python
  EXTENSION_MAP = {
    "Images":    [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".doc"],
    "Installer": [".exe", ".msi"],
    "Archives":  [".zip", ".rar", ".7z"],
    "Code":      [".py", ".c", ".cpp", ".js", ".html", ".java", ".md", ".h"],
    "Video":     [".mp4", ".mp3"]
}
  ```
**Feel free to add other extensions.**

### 2. `organize_files()` Function
This function performs the actual work. It:
1.  Scans the directory.
2.  Matches files against the `EXTENSION_MAP`.
3.  Moves matched files to their specific folders.
4.  Moves any unmatched files into an **"Others"** folder to keep the main directory clean.

### 3. `DownloadHandler` Class
This uses the `watchdog` library to monitor file system events in real-time.
* **Batching:** It uses a `file_buffer` to count changes. It waits until **10 files** are modified/created before running, preventing the script from running 100 times for 100 small files.

### 4. The Main Loop (Timeouts)
The script doesn't just wait for 10 files; it also has a **Timeout** safety net.
* **Logic:** If you download 3 files (filling the buffer partially) and stop, the script waits for **300 seconds (5 minutes)** of silence.
* **Result:** After the timeout, it organizes whatever is currently in the buffer, ensuring no files get stuck waiting forever.

---

## 🚀 How to Run
1.  Install dependencies: `pip install watchdog`
2.  Open Task scheduler on windows
3.  Add a new task and assign the program's directory
4.  Provide a full path for your (`pythonw.exe`) on windows,
    and on Linux you provide the full path to (`python`) or (`python3`) and add '&' at the end.
    For example:
   ```bash
   @reboot /usr/bin/python3/<your_home>/<Name>/Downloads/organize_files.py &
   ```
