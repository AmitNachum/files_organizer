import time
import os
import shutil
from watchdog import observers
from watchdog.events import FileSystemEventHandler

# Paths and Configurations
DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

# Maps file types to specific folder names
EXTENSION_MAP = {
    "Images":    [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".doc"],
    "Installer": [".exe", ".msi"],
    "Archives":  [".zip", ".rar", ".7z"],
    "Code":      [".py", ".c", ".cpp", ".js", ".html", ".java", ".md", ".h"],
    "Video":     [".mp4", ".mp3"]
}

def not_a_file(contender: str) -> bool:
    """Checks if the path is a directory (and thus should be skipped)."""
    return os.path.isdir(contender)

def organize_files():
    """
    Scans the download directory and moves files into subfolders based on extension.
    Any file not matched in the map is moved to an 'Others' folder.
    """
    print(f"--- Organizing folder: {DOWNLOAD_PATH} ---")

    # 1. Categorized Move Loop
    for file_name in os.listdir(DOWNLOAD_PATH):
        og_file_path = os.path.join(DOWNLOAD_PATH, file_name)
        
        # Skip directories and the script itself to prevent crashing
        if os.path.isdir(og_file_path) or file_name == os.path.basename(__file__):
            continue
        
        _, extension = os.path.splitext(file_name)

        # Check against our map
        for folder_name, ext_list in EXTENSION_MAP.items():
            if extension.lower() in ext_list:
                destination_dir = os.path.join(DOWNLOAD_PATH, folder_name)
                os.makedirs(destination_dir, exist_ok=True)
                
                final_path = os.path.join(destination_dir, file_name)
                try:
                    shutil.move(og_file_path, final_path)
                    print(f"Moved: {file_name} -> {folder_name}")
                except Exception as e:
                    print(f"Error moving {file_name}: {e}")
                
                # Break inner loop so we don't check other categories for this file
                break

    # 2. Uncategorized 'Others' Loop
    # We rescan to catch anything left over
    for other_file in os.listdir(DOWNLOAD_PATH):
        old_path = os.path.join(DOWNLOAD_PATH, other_file)

        # Safety checks: Is it a dir? Is it this script?
        if not_a_file(old_path) or other_file == os.path.basename(__file__):
            continue
        
        dest_dir = os.path.join(DOWNLOAD_PATH, "Others")
        os.makedirs(dest_dir, exist_ok=True)      

        fin_path = os.path.join(dest_dir, other_file)
        try:
            shutil.move(old_path, fin_path)
            print(f"Moved to Others: {other_file}")
        except Exception as e:
            # File might have been moved in the previous loop, so errors are expected here
            pass

    print("--- Organization Cycle Complete ---\n")


class DownloadHandler(FileSystemEventHandler):
    """
    Watchdog handler that buffers events to prevent rapid-fire execution.
    """
    def __init__(self) -> None:
        super().__init__()
        self.file_buffer = set()
        self.BATCH_SIZE = 10        
        self.last_event_time = time.time()
        self.dont_care = {'.crdownload', '.tmp', '.part'}
        print("==== WatchDog Initialized ====\n")

    def is_temp_file(self, filepath):
        """Ignored temporary browser files."""
        _, suffix = os.path.splitext(filepath)
        if suffix in self.dont_care:
            return True
        return False  

    def process_event_count(self):
        """Checks if buffer is full enough to trigger immediate organization."""
        current_count = len(self.file_buffer)
        print(f"Buffer: {current_count}/{self.BATCH_SIZE} changes detected...")

        if current_count >= self.BATCH_SIZE:
            print("BATCH LIMIT REACHED: Triggering Organization.")
            self.flush_buffer()
            
    def flush_buffer(self):
        """Executes the organization logic and clears the counter."""
        organize_files()
        self.file_buffer.clear()

    def on_created(self, event):
        if not event.is_directory and not self.is_temp_file(event.src_path):
            self.last_event_time = time.time()
            self.file_buffer.add(event.src_path)
            self.process_event_count()

    def on_modified(self, event):
         if not event.is_directory and not self.is_temp_file(event.src_path):
            self.last_event_time = time.time()
            self.file_buffer.add(event.src_path)
            self.process_event_count()

    def on_moved(self, event):
        if not event.is_directory and not self.is_temp_file(event.dest_path):
            self.last_event_time = time.time()
            self.file_buffer.add(event.dest_path)
            self.process_event_count()

if __name__ == "__main__":
    # Setup Watchdog
    event_handler = DownloadHandler()
    obs = observers.Observer()
    obs.schedule(event_handler, DOWNLOAD_PATH, recursive=False)
    obs.start()

    TIMEOUT_SET = 300  # 300 seconds = 5 minutes
    fresh_org = True
    print(f"Running! Organizing every 10 files OR every {TIMEOUT_SET} seconds of silence.")

    try:
        while True:
            time.sleep(1)
            
            # Run once on startup
            if fresh_org:
                event_handler.flush_buffer()
                fresh_org = False
            
            # Check for Timeout (Silence)
            if len(event_handler.file_buffer) > 0:
                time_diff = time.time() - event_handler.last_event_time
                
                if time_diff >= TIMEOUT_SET:
                    print(f"Timeout ({TIMEOUT_SET}s) reached - Organizing pending files.")
                    event_handler.flush_buffer()
                    
    except KeyboardInterrupt:
        obs.stop()
    
    obs.join()