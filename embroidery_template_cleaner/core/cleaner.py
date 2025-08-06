from pathlib import Path
from typing import Generator, List, Callable

from .configuration import Configuration, DISPLAY_FILE_EXTENSIONS
from .events import (
    Event,
    Response,
    StatusUpdate,
    RequestConfirmation,
    UserConfirmationResponse,
    RequestRetrySkipAbort,
    RetrySkipAbortResponse,
    RetrySkipAbortChoice
)

# --- Type Definitions ---
type SubGenerator = Generator[Event, Response, None]
type MainGenerator = Generator[Event, Response, int]

class OperationAbortedError(Exception):
    """Raised when the user chooses to abort the operation."""
    pass

# --- Helper generator for Retry/Skip/Abort ---

def _retryable_operation_generator(
    operation: Callable[[], None],
    operation_description: str,
    path: Path,
) -> SubGenerator:
    """
    A generic generator that executes a given operation and handles OSErrors
    by yielding a RequestRetrySkipAbort event, allowing the user to decide
    how to proceed.

    Args:
        operation: A no-argument function that performs the I/O.
        operation_description: A human-readable string for the dialog.
        path: The file path involved in the operation.
    """
    while True:
        try:
            operation()
            return # Success, exit the generator
        except OSError as e:
            # The operation failed, ask the user what to do.
            response: RetrySkipAbortResponse = yield RequestRetrySkipAbort(
                operation_description=operation_description,
                path=str(path),
                error_message=str(e)
            )
            if response.choice == RetrySkipAbortChoice.ABORT:
                raise OperationAbortedError("User aborted the operation.")
            if response.choice == RetrySkipAbortChoice.SKIP:
                return # User chose to skip, exit the generator
            # If RETRY, the loop continues and the operation is attempted again.

# --- Sub-generator for Directory Emptiness Check ---

def _is_directory_empty_and_confirm(path: Path) -> Generator[Event, Response, bool]:
    """
    A generator that checks if a directory is empty or only contains display files.
    If it only contains display files, it yields a RequestConfirmation.
    Returns True if the directory is or becomes empty, False otherwise.
    """
    if not path.is_dir():
        return False

    try:
        items = list(path.iterdir())
    except PermissionError:
        yield StatusUpdate(message=f"Permission error reading {path}. Skipping.")
        return False

    if not items:
        return True

    display_files = [item for item in items if item.is_file() and item.suffix.lower() in DISPLAY_FILE_EXTENSIONS]
    
    if len(display_files) == len(items):
        response: Response = yield RequestConfirmation(
            path=str(path),
            files_in_dir=[f.name for f in display_files]
        )

        yield StatusUpdate(message=repr(response))

        if not response.accepted:
            yield StatusUpdate(message=f"Skipping deletion of display files in {path.name}.")
            return False

        yield StatusUpdate(message=f"Deleting display files in {path.name}...")
        # Note: We don't need the count back from this, so we just yield from it.
        yield from _delete_matching_files_generator(
            all_paths=display_files,
            extensions_to_delete=DISPLAY_FILE_EXTENSIONS
        )

        # After deletion, check if the directory is now actually empty.
        try:
            return not any(path.iterdir())
        except PermissionError:
            yield StatusUpdate(message=f"Permission error after display file deletion in {path}.")
            return False

    return False


# --- Sub-generator for File Deletion Pass ---

def _delete_matching_files_generator(all_paths: List[Path], extensions_to_delete: set[str]) -> MainGenerator:
    """
    Iterates over a given list of paths and deletes files matching the extensions.
    Returns the count of deleted files.
    """
    deleted_files_count = 0
    for path in all_paths:
        if not (path.is_file() and path.exists()):
            continue

        if path.suffix.lower() in extensions_to_delete or path.name.lower() in extensions_to_delete:
            yield from _retryable_operation_generator(
                operation=path.unlink,
                operation_description=f"deleting file '{path.name}'",
                path=path
            )
            deleted_files_count += 1
            yield StatusUpdate(message=f"Deleted: {path.name}")

    return deleted_files_count


# --- Sub-generator for Empty Directory Cleanup Pass ---

def _cleanup_empty_directories_generator(all_paths: List[Path]) -> SubGenerator:
    """
    Cleans up empty directories from a given list of paths.
    """
    all_dirs = [p for p in all_paths if p.is_dir() and p.exists()]
    all_dirs.sort(key=lambda p: len(p.parts), reverse=True)

    for path in all_dirs:

        is_empty = yield from _is_directory_empty_and_confirm(path)

        if is_empty:
            yield StatusUpdate(message=f"Removing empty directory: {path.name}")
            yield from _retryable_operation_generator(
                operation=path.rmdir,
                operation_description=f"removing directory '{path.name}'",
                path=path
            )


# --- Main Orchestrator Generator ---

def clean_directory_generator(config: Configuration) -> MainGenerator:
    """
    Main generator that orchestrates the cleaning process by calling sub-generators.
    """
    if not config.target_directory:
        return 0

    yield StatusUpdate(message="Scanning all items in target directory...")
    try:
        all_paths = list(config.target_directory.rglob("*"))
    except Exception as e:
        yield StatusUpdate(message=f"Fatal error scanning directory: {e}")
        return 0

    # Pass 1: Delete matching files
    yield StatusUpdate(message=f"Found {len(all_paths)} items. Deleting specified file types...")
    deleted_files_count = yield from _delete_matching_files_generator(
        all_paths=all_paths,
        extensions_to_delete=config.extensions_to_delete
    )

    # Pass 2: Clean up empty directories
    yield StatusUpdate(message="Cleaning up empty directories...")
    yield from _cleanup_empty_directories_generator(all_paths=all_paths)

    return deleted_files_count