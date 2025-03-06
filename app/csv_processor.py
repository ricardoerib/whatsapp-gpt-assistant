import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

csv_data = None

def process_csv():
    global csv_data
    try:
        csv_data = pd.read_csv("./data/vx_questions_results.csv")
        logger.info("Survey data read successfully!")
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return

class CSVHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("./data/vx_questions_results.csv"):
            process_csv()

def start_csv_watcher():
    event_handler = CSVHandler()
    observer = Observer()
    observer.schedule(event_handler, path="./data/", recursive=False)
    observer.start()
