from pathlib import Path
import json
import tkinter

from dataclasses import dataclass

CONFIG_FILE_LOCATION = Path.home() / 'sewing_file_cleaner.config.json'

SEWING_FILE_EXTENSIONS = {
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
    '.DS_Store',
}

@dataclass
class Configuration:
    target_directory: Path
    extension_blacklist: set[str]

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

        target_directory = Path(config_dict['target_directory'])
        if not target_directory.exists():
            raise ValueError(f"Target directory {target_directory} does not exist!")
        if not target_directory.is_dir():
            raise ValueError(f"Target directory {target_directory} is not a directory.")
        
        extension_blacklist = set(config_dict['extension_blacklist'])
        if extension_blacklist - SEWING_FILE_EXTENSIONS != {}:
            raise ValueError(f"Extension blacklist contains unrecognized extensions {extension_blacklist - SEWING_FILE_EXTENSIONS}.")

        return Configuration(target_directory=target_directory, extension_blacklist=extension_blacklist)
    
    def to_json(self) -> str:
        return json.dumps({
            'target_directory': str(self.target_directory.resolve()),
            'extension_blacklist': list(self.extension_blacklist)
        })

def is_directory_empty(path: Path) -> bool:
    assert path.is_dir()
    assert path.exists()
    return not any(path.iterdir())

def delete_and_clean_empty_directories(file_to_delete: Path):
    # delete the file
    file_to_delete.unlink()

    # walk upwards, deleting empty directories left by this deletion
    current = file_to_delete.parent
    while is_directory_empty(current):
        current.rmdir()
        current = current.parent

def delete_files_by_extension(target_directory: Path, extensions_to_delete: set[str]):
    for file_to_delete in target_directory.rglob(f"*"):
        if not file_to_delete.is_file():
            continue
        if file_to_delete.suffix not in extensions_to_delete:
            continue
        delete_and_clean_empty_directories(file_to_delete=file_to_delete)

def main():
    # load config
    if CONFIG_FILE_LOCATION.exists():
        config = Configuration.from_json(CONFIG_FILE_LOCATION)
    else:
        config = Configuration(target_directory=None, extension_blacklist=set())
    
    # TODO: write gui to set target dir and blacklisted file extensions
    


    # save config for next time
    CONFIG_FILE_LOCATION.write_text(config.to_json())

if __name__ == '__main__':
    main()


# TODO: package it with pyinstaller for Windows and MacOS