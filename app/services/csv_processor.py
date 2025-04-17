import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional  # Adicionando as importações necessárias
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Global variable to hold CSV data
csv_data = None

def process_csv() -> None:
    """
    Process CSV file and store it in global variable
    
    This function reads the CSV file specified in settings and stores
    the data in a global variable for use by other parts of the application.
    """
    global csv_data
    try:
        # Get CSV file path from settings
        csv_path = settings.CSV_FILE_PATH
        
        # Check if file exists
        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found at {csv_path}")
            return
            
        # Read CSV file into pandas DataFrame
        csv_data = pd.read_csv(csv_path)
        logger.info(f"CSV data read successfully from {csv_path}")
        logger.info(f"CSV data shape: {csv_data.shape}")
        
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        csv_data = None

class CSVHandler(FileSystemEventHandler):
    """
    File system event handler for CSV file changes
    
    This class watches for changes to the CSV file and automatically
    reloads the data when the file is modified.
    """
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory and event.src_path.endswith(settings.CSV_FILE_PATH):
            logger.info(f"CSV file modified: {event.src_path}")
            process_csv()
            
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory and event.src_path.endswith(settings.CSV_FILE_PATH):
            logger.info(f"CSV file created: {event.src_path}")
            process_csv()

def start_csv_watcher() -> None:
    """
    Start the CSV file watcher
    
    This function sets up a file system watcher to monitor changes
    to the CSV file and reload the data when changes are detected.
    """
    try:
        # Get directory containing CSV file
        csv_dir = os.path.dirname(settings.CSV_FILE_PATH)
        
        # Create directory if it doesn't exist
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
            logger.info(f"Created directory: {csv_dir}")
            
        # Set up file system observer
        event_handler = CSVHandler()
        observer = Observer()
        observer.schedule(event_handler, path=csv_dir, recursive=False)
        observer.start()
        
        logger.info(f"CSV watcher started for directory: {csv_dir}")
        
    except Exception as e:
        logger.error(f"Error starting CSV watcher: {e}")

class CSVProcessor:
    """Service for CSV data processing"""
    
    def __init__(self):
        """Initialize the CSV processor"""
        self.logger = logging.getLogger(__name__)
        
    def get_csv_data(self) -> pd.DataFrame:
        """Get the CSV data"""
        global csv_data
        return csv_data
        
    def query_data(self, query: str) -> pd.DataFrame:
        """
        Query the CSV data based on keywords
        
        Args:
            query: The search query
            
        Returns:
            DataFrame containing matching rows
        """
        global csv_data
        
        if csv_data is None:
            self.logger.warning("No CSV data available")
            return pd.DataFrame()
            
        try:
            # Simple implementation: search for query in all string columns
            result = csv_data[csv_data.astype(str).apply(
                lambda row: row.str.contains(query, case=False, na=False).any(),
                axis=1
            )]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error querying CSV data: {e}")
            return pd.DataFrame()
            
    def get_column_stats(self, column_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific column
        
        Args:
            column_name: The name of the column
            
        Returns:
            Dictionary of statistics
        """
        global csv_data
        
        if csv_data is None:
            self.logger.warning("No CSV data available")
            return {}
            
        if column_name not in csv_data.columns:
            self.logger.warning(f"Column '{column_name}' not found in CSV data")
            return {}
            
        try:
            # Get column statistics
            stats = csv_data[column_name].describe().to_dict()
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting column statistics: {e}")
            return {}