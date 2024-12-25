from pathlib import Path
import json

CONFIG_FILE_LOCATION = Path.home() / 'embroidery_template_cleaner.config.json'

DISPLAY_FILE_EXTENSIONS = {
    '.pdf',
    '.png',
    '.jpg',
}

class Configuration:
    target_directory: Path
    
    def __init__(self, target_directory: Path):
        if target_directory:
            if not target_directory.exists():
                raise ValueError(f"Target directory {target_directory} does not exist!")
            if not target_directory.is_dir():
                raise ValueError(f"Target directory {target_directory} is not a directory.")

        self.target_directory = target_directory