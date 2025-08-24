# core_library/data_sinks.py
import json
from pathlib import Path
from typing import Dict, Any

class JSONDataSink:
    """
    A simple data sink that writes dictionaries to a JSON Lines (.jsonl) file.

    Each record is a single line in the file, making it easy to append
    and read, even for large logs.
    """
    def __init__(self, log_path: Path):
        """
        Initializes the sink with the path to the log file.
        """
        self.log_path = log_path
        # Ensure the directory for the log file exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, data: Dict[Any, Any]):
        """
        Serializes a dictionary to a JSON string and appends it as a new
        line to the log file.
        """
        try:
            # Open the file in 'append' mode with text encoding
            with open(self.log_path, 'a', encoding='utf-8') as f:
                # Convert the dictionary to a JSON string
                json_string = json.dumps(data)
                # Write the string followed by a newline character
                f.write(json_string + '\n')
        except Exception as e:
            print(f"Error writing to data sink {self.log_path}: {e}")