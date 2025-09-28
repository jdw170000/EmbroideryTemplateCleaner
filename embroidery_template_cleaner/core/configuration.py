import json
from pathlib import Path

CONFIG_FILE_LOCATION = Path.home() / 'embroidery_template_cleaner.config.json'
LOG_FILE_LOCATION = Path.home() / 'embroidery_template_cleaner.log'

TEMPLATE_FILE_EXTENSIONS = {
    '.exp', 
    '.hus', 
    '.jef', 
    '.pcs', 
    '.rgb', 
    '.sew', 
    '.vip',
    '.vp3', 
    '.xxx', 
    '.shv', 
    '.csd', 
    '.art', 
    '.jan', 
    '.edr',
    '.emb', 
    '.inf', 
    '.pec', 
    '.pes', 
    '.dst', 
    '.ds_store',
}

DISPLAY_FILE_EXTENSIONS = {
    '.pdf', 
    '.png', 
    '.jpg',
}


class Configuration:
    target_directory: Path | None
    extensions_to_delete: set[str]
    
    def __init__(self, target_directory: Path | None, extensions_to_delete: set[str]):
        if target_directory:
            if not target_directory.exists():
                raise ValueError(f"Target directory does not exist: {target_directory}")
            if not target_directory.is_dir():
                raise ValueError(f"Target path is not a directory: {target_directory}")

        unrecognized_exts = extensions_to_delete - (TEMPLATE_FILE_EXTENSIONS | DISPLAY_FILE_EXTENSIONS)
        if unrecognized_exts:
            raise ValueError(f"Unrecognized extensions provided: {unrecognized_exts}")
        
        self.target_directory = target_directory
        self.extensions_to_delete = extensions_to_delete

    @staticmethod
    def from_json_file(json_path: Path) -> 'Configuration':
        """Loads configuration from a JSON file."""
        try:
            config_dict = json.loads(json_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ValueError(f"Could not read or parse config file: {json_path}\n{e}")

        target_dir_str = config_dict.get('target_directory')
        extensions = set(config_dict.get('extensions_to_delete', []))

        target_dir = Path(target_dir_str) if target_dir_str else None
        
        return Configuration(target_directory=target_dir, extensions_to_delete=extensions)
    
    def to_json_str(self) -> str:
        """Serializes the configuration to a JSON string."""
        return json.dumps({
            'target_directory': str(self.target_directory.resolve()) if self.target_directory else '',
            'extensions_to_delete': sorted(list(self.extensions_to_delete))
        }, indent=2)

def load_config() -> Configuration:
    if CONFIG_FILE_LOCATION.exists():
        try:
            return Configuration.from_json_file(CONFIG_FILE_LOCATION)
        except ValueError:
            # If config is corrupt, load a safe default.
            pass
    return Configuration(target_directory=None, extensions_to_delete=set())

def save_config(config: Configuration):
    """Saves the given configuration to the default location."""
    CONFIG_FILE_LOCATION.write_text(config.to_json_str())