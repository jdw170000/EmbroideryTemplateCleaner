from pathlib import Path
from config import Configuration

def is_directory_empty(path: Path) -> bool:
    assert path.is_dir()
    assert path.exists()
    return not any(path.iterdir())

def delete_and_clean_empty_directories(file_to_delete: Path, top_directory: Path = None):
    # delete the file
    file_to_delete.unlink()

    # walk upwards, deleting empty directories left by this deletion
    current = file_to_delete.parent
    while is_directory_empty(current):
        if current == top_directory:
            break
        current.rmdir()
        current = current.parent

def delete_files_by_extension(target_directory: Path, extensions_to_delete: set[str]) -> int:
    if target_directory is None:
        return 0
    
    deleted_files = 0
    for file_to_delete in target_directory.rglob(f"*"):
        if not file_to_delete.is_file():
            continue
        if file_to_delete.name.startswith('.'):
            if file_to_delete.name.lower() not in extensions_to_delete:
                continue
        elif file_to_delete.suffix.lower() not in extensions_to_delete:
            continue
        delete_and_clean_empty_directories(file_to_delete=file_to_delete, top_directory=target_directory)
        deleted_files += 1
    
    return deleted_files

def clean_directory(config: Configuration) -> int:
    return delete_files_by_extension(config.target_directory, config.extensions_to_delete)