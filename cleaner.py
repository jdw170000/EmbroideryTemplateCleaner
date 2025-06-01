from pathlib import Path
from config import Configuration, DISPLAY_FILE_EXTENSIONS
import queue

def is_directory_empty(path: Path, update_queue: queue.Queue, response_queue: queue.Queue) -> bool:
    if not path.exists():
        return True
    if not path.is_dir():
        return False 

    try:
        directory_contents = list(path.iterdir())
    except PermissionError:
        update_queue.put({'type': 'status', 'message': f"Permission error for {path}. Assuming not empty."})
        return False

    if not directory_contents:
        return True
    
    # also treat the folder as empty if it only contains display file extensions
    only_display_files = True
    display_file_items = []
    for item in directory_contents:
        if not (item.is_file() and item.suffix.lower() in DISPLAY_FILE_EXTENSIONS):
            only_display_files = False
            break
        display_file_items.append(item)

    if only_display_files:
        update_queue.put({
            'type': 'confirm_empty_dir',
            'path': str(path),
            'files': [f.name for f in display_file_items]
        })
        user_says_delete_dir_and_contents = response_queue.get() # Blocks worker until GUI responds
        
        if not user_says_delete_dir_and_contents:
            return False
        
        for file_to_delete_display in display_file_items:
            try:
                update_queue.put({'type': 'status', 'message': f"Deleting display file: {file_to_delete_display.name}"})
                file_to_delete_display.unlink()
            except OSError as e:
                update_queue.put({'type': 'status', 'message': f"Could not delete {file_to_delete_display.name}: {e}"})
        
        try:
            return not any(path.iterdir())
        except PermissionError:
             update_queue.put({'type': 'status', 'message': f"Permission error for {path} after display file deletion."})
             return False

    return False

def delete_and_clean_empty_directories(file_to_delete: Path, top_directory: Path, update_queue: queue.Queue, response_queue: queue.Queue):
    update_queue.put({'type': 'status', 'message': f"Processing: {file_to_delete.name}"})
    try:
        file_to_delete.unlink()
        update_queue.put({'type': 'status', 'message': f"Deleted: {file_to_delete.name}"})
    except OSError as e:
        update_queue.put({'type': 'status', 'message': f"Error deleting {file_to_delete.name}: {e}. Skipping."})
        return

    # walk upwards, deleting empty directories left by this deletion
    current = file_to_delete.parent
    while current and current.exists() and current.is_dir() and current != current.parent:
        # stop when there is a non-empty directory
        if not is_directory_empty(current, update_queue, response_queue):
            break

        # don't walk above the target directory
        if current.resolve() == top_directory.resolve():
            break

        try:
            current.rmdir()
            update_queue.put({'type': 'status', 'message': f"Removed empty directory: {current.name}"})
        except OSError as e:
            update_queue.put({'type': 'status', 'message': f"Could not remove {current.name}: {e}."})
            break
        
        current = current.parent

def delete_files_by_extension(target_directory: Path, extensions_to_delete: set[str], update_queue: queue.Queue, response_queue: queue.Queue) -> int:
    if target_directory is None:
        return 0
    
    update_queue.put({'type': 'status', 'message': "Scanning directory for files..."})
    try:
        all_paths_to_check = list(target_directory.rglob("*"))
    except Exception as e:
        update_queue.put({'type': 'error', 'message': f"Error scanning directory {target_directory}: {e}"})
        return 0

    update_queue.put({'type': 'status', 'message': f"Found {len(all_paths_to_check)} items. Processing..."})

    deleted_files_count = 0
    
    for item_path in all_paths_to_check:
        if not item_path.exists():
            continue
        
        if not item_path.is_file():
            continue

        # Determine if the file matches the criteria for deletion
        should_delete = False
        if item_path.name.startswith('.'): # Hidden files like .DS_Store
            if item_path.name.lower() in extensions_to_delete:
                should_delete = True
        elif item_path.suffix.lower() in extensions_to_delete: # Regular files by suffix
            should_delete = True
        
        if should_delete:
            delete_and_clean_empty_directories(file_to_delete=item_path, top_directory=target_directory, update_queue=update_queue, response_queue=response_queue)
            deleted_files_count += 1
    
    return deleted_files_count

def clean_directory(config: Configuration, update_queue: queue.Queue, response_queue: queue.Queue) -> int:
    if not config.target_directory:
        return 0
    return delete_files_by_extension(config.target_directory, config.extensions_to_delete, update_queue, response_queue)