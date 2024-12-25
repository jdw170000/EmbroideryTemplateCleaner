from pathlib import Path
import json

CONFIG_FILE_LOCATION = Path.home() / 'embroidery_template_cleaner.config.json'

# file extensions will be cast to lowercase before comparsion
TEMPLATE_FILE_EXTENSIONS = {
    '.exp',
    '.hus',
    '.jef',
    '.pcs',
    '.sew',
    '.vip',
    '.vp3',
    '.xxx',
    '.shv',
    '.csd',
    '.art',
    '.jan',
    '.edr',
    '.inf',
    '.pec',
    '.pes',
    '.dst',
    '.ds_store',
}

class Configuration:
    target_directory: Path
    extensions_to_delete: set[str]
    
    def __init__(self, target_directory: Path, extensions_to_delete: set[str]):
        if target_directory:
            if not target_directory.exists():
                raise ValueError(f"Target directory {target_directory} does not exist!")
            if not target_directory.is_dir():
                raise ValueError(f"Target directory {target_directory} is not a directory.")

        if extensions_to_delete:
            if len(extensions_to_delete - TEMPLATE_FILE_EXTENSIONS) > 0:
                raise ValueError(f"Extension blacklist contains unrecognized extensions {extensions_to_delete - TEMPLATE_FILE_EXTENSIONS}.")
        
        self.target_directory = target_directory
        self.extensions_to_delete = extensions_to_delete

    @staticmethod
    def from_json(json_path: Path) -> 'Configuration':
        config_dict = json.loads(json_path.read_bytes())
        if not 'target_directory' in config_dict:
            raise ValueError(f"{json_path} does not include a 'target_directory'.")
        if not isinstance(config_dict['target_directory'], str):
            raise ValueError(f"Target directory ({config_dict['target_directory']}) should be a string.")
        if not 'extension_blacklist' in config_dict:
            raise ValueError(f"{json_path} does not include an 'extension_blacklist'.")
        if not isinstance(config_dict['extension_blacklist'], list):
            raise ValueError(f"Extension blacklist ({config_dict['extension_blacklist']}) should be a list of strings.")

        target_directory = Path(config_dict['target_directory']) if config_dict['target_directory'] else None
        extension_blacklist = set(config_dict['extension_blacklist'])

        return Configuration(target_directory=target_directory, extensions_to_delete=extension_blacklist)
    
    def to_json(self) -> str:
        return json.dumps({
            'target_directory': str(self.target_directory.resolve() if self.target_directory else ''),
            'extension_blacklist': list(self.extensions_to_delete)
        })

def load_config() -> Configuration:
    if CONFIG_FILE_LOCATION.exists():
        return Configuration.from_json(CONFIG_FILE_LOCATION)
    return Configuration(target_directory=None, extensions_to_delete=set())

def save_config(config: Configuration):
    CONFIG_FILE_LOCATION.write_text(config.to_json())