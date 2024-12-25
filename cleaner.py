from pathlib import Path
from config import Configuration, DISPLAY_FILE_EXTENSIONS
from tkinter import messagebox

def is_directory_empty(path: Path) -> bool:
    assert path.is_dir()
    assert path.exists()
    
    directory_contents = list(path.iterdir())
    if not directory_contents:
        return True
    
    # also treat the folder as empty if it only contains display file extensions
    if all(file.is_file() and file.suffix.lower() in DISPLAY_FILE_EXTENSIONS for file in path.iterdir()):
        # this might not actually be empty; ask the user to confirm
        formatted_content = '\n'.join(f'\t{file.name}' for file in directory_contents)
        user_says_directory_empty = messagebox.askyesno(
            title='Folder Deletion Confirmation',
            message=f'{path} only contains display files:\n{formatted_content}\n\nDo you want to delete it?'
        )
        if not user_says_directory_empty:
            return False
        
        # clean up the files to be deleted
        for file in directory_contents:
            file.unlink()
        
        return True

    return False

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
    for file_to_delete in list(target_directory.rglob(f"*")):
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