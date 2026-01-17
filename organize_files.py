import time
import os
import shutil
from watchdog import observers
from watchdog.events import DirModifiedEvent, DirMovedEvent, FileModifiedEvent, FileMovedEvent, FileSystemEventHandler



# Load the path of download's directory.
download_path = os.path.join(os.path.expanduser("~"),"Downloads")


# Create a hash map where {Key = File Kind : list of suffix for that type}

extension_map ={
    "Images" :  [".jpg", ".jpeg",".png", ".gif", ".webp"],
    "Documents": [".pdf",".docx",".txt",".xlsx",".pptx",".doc"],
    "Installer": [".exe", ".msi"],
    "Archives" : [".zip",".rar",".7z"],
    "Code" : [".py",".c",".cpp",".js",".html",".java",".md",".h"],
    "Video" : [".mp4",".mp3"]
}



def not_a_file(contender : str ) -> bool:
    return os.path.isdir(contender)


def organize_files():

    print(f"Watching folder: {download_path}")

    # Start traversing for each file in the downloads
    for file_name in os.listdir(download_path):
        # Get the file/folder full path 
        og_file_path = os.path.join(download_path, file_name)
        # Check if the current object is a file if not skip it
        if os.path.isdir(og_file_path):
            continue
        
        # Split the file name and its extension
        prefix_file_name, extension = os.path.splitext(file_name)

        for folder_name , ext_list in extension_map.items():
            
            # Check whether the extension is in the current list use lower for JPEG
            if extension.lower() in ext_list:
                
                # Get the correct and adequate directory
                destination_dir = os.path.join(download_path,folder_name)
                # If it does not exist yet create it
                os.makedirs(destination_dir, exist_ok = True)
                
                final_path = os.path.join(destination_dir,file_name)
                # Try and Move the file to the currect directory
                try:
                    shutil.move(og_file_path,final_path)
                    print(f"\nMoved: {file_name}  ---->  {final_path}")
                except Exception as excep:
                    print(f"Error Moving {file_name}: {excep}")
                
                # Stop checking for this file
                break


    for other_file in os.listdir(download_path):

        old_path = os.path.join(download_path,other_file)

        if not_a_file(old_path):
                continue
        
        # Attach to the current directory an addition path to the new Default directory
        dest_dir = os.path.join(download_path, "Others")

        # Create a default directory for other less common files
        os.makedirs(dest_dir,exist_ok=True)      

        fin_path = os.path.join(dest_dir,other_file)

        try:
            shutil.move(old_path,fin_path)
            print(f"\nMoved: {other_file} ----> {fin_path}")
        except Exception as e:
            print(f"Error Moving {other_file}: {e}")

    print("Done organizing!")


import time
import os
import shutil
from watchdog import observers
from watchdog.events import FileSystemEventHandler

# ... [Keep your existing path and map setup here] ...
# ... [Keep your organize_files() function here, BUT FIX LINE 74] ...

# -----------------
# BATCH WATCHDOG
# -----------------
class DownloadHandler(FileSystemEventHandler):

    def __init__(self) -> None:
        super().__init__()
        # We use a SET because it automatically ignores duplicates.
        # If 'test.txt' triggers 5 events, it's still just one entry in the set.
        self.file_buffer = set()
        self.BATCH_SIZE = 10        
        self.last_event_time = time.time()
        self.dont_care = {'.crdownload','.tmp','.part'}
        print("==== WatchDog created ====\n")

    def is_temp_file(self,filepath):
        name, suffix = os.path.splitext(filepath)
        if suffix in self.dont_care:
            print(f"{filepath} is a temp file no need for that")
            return True
        return False  

    def process_event_count(self, event):
        """Helper to add files to buffer and check size"""
        current_count = len(self.file_buffer)
        print(f"Buffer: {current_count}/{self.BATCH_SIZE} files waiting...")

        # If we reached the target, release the kraken!
        if current_count >= self.BATCH_SIZE :
            print("\n--- BATCH LIMIT REACHED: ORGANIZING NOW ---")
            self.flush_buffer()
            
    def flush_buffer(self):
        organize_files()
                
        # Clear the buffer so we wait for the next 10
        self.file_buffer.clear()

    def on_created(self, event):
        if not event.is_directory and not self.is_temp_file(event.src_path):
            self.last_event_time = time.time()
            self.file_buffer.add(event.src_path)
            self.process_event_count(event)
        

    def on_modified(self, event):
         if not event.is_directory and not self.is_temp_file(event.src_path):
            self.last_event_time = time.time()
            self.file_buffer.add(event.src_path)
            self.process_event_count(event)

    def on_moved(self, event):
        if not event.is_directory and not self.is_temp_file(event.dest_path):
            self.last_event_time = time.time()
            self.file_buffer.add(event.dest_path)
            self.process_event_count(event)
# ----- MAIN EXECUTION -----

if __name__ == "__main__":

    #---- Observer and Handler init ----
    event_handler = DownloadHandler()
    obs = observers.Observer()
    obs.schedule(event_handler, download_path, recursive=False)
    obs.start()

    #---- Observer and Handler init ----

    TIMEOUT_SET = 5  # seconds
    fresh_org = True
    print(f"Running! Organizing every 10 files OR every {TIMEOUT_SET} seconds.")

    # ==== Main Loop =====

    try:
        while True:
            time.sleep(1) # Sleep first to save CPU
            if fresh_org:
                print("=== Fresh Start executing === ")
                event_handler.flush_buffer()
                fresh_org = False
            # --- FIX IS HERE ---
            # 1. Check if we actually have files waiting!
            if len(event_handler.file_buffer) > 0:
                
                # 2. THEN check the time
                time_diff = time.time() - event_handler.last_event_time
                
                if time_diff >= TIMEOUT_SET:
                    print(f"=== Time out ({TIMEOUT_SET}s) - Organizing {len(event_handler.file_buffer)} files ===")
                    event_handler.flush_buffer()
    except KeyboardInterrupt:
        obs.stop()
    obs.join()

    # ==== Main Loop =====
