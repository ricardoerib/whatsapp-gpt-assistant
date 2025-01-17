import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.utils import merge_duplicates
# from app.email_notifier import send_email
csv_data = None

def process_csv():
    global csv_data
    csv_data = pd.read_csv("./data/vx_questions_results.csv")
    # df = merge_duplicates(df)
    # df.to_csv("./data/data_processed.csv", index=False)

class CSVHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("vx_questions_results.csv"):
            process_csv()
            # send_email("CSV Updated", "The CSV file has been updated and processed.")

def start_csv_watcher():
    event_handler = CSVHandler()
    observer = Observer()
    observer.schedule(event_handler, path="data/", recursive=False)
    observer.start()
