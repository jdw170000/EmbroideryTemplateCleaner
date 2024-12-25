from pathlib import Path
from config import Configuration, DISPLAY_FILE_EXTENSIONS

import tkinter as tk
from tkinter import ttk

def scrollable_askyesno(title: str, header: str, scrollable_content: str) -> bool:
    """
    Creates a scrollable yes/no dialog box.

    Args:
        title: The title of the dialog box.
        header: The header text displayed above the scrollable content.
        scrollable_content: The text content that will be placed in a scrollable area.

    Returns:
        True if the user clicks "Yes", False otherwise.
    """

    class ScrollableDialog:
        def __init__(self, parent, title, header, content):
            self.result = False

            self.top = tk.Toplevel(parent)
            self.top.title(title)
            self.top.resizable(False, False)

            # Header Label
            header_label = ttk.Label(self.top, text=header, wraplength=400, justify="left", font=("Arial", 10, "bold"))
            header_label.pack(padx=10, pady=10)

            # Frame for Scrollable Content
            frame = ttk.Frame(self.top)
            frame.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)

            # Canvas for Scrollbar
            canvas = tk.Canvas(frame, highlightthickness=0)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Configure Canvas
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

            # Inner Frame for Content
            content_frame = ttk.Frame(canvas)
            canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

            # Content Label
            content_label = ttk.Label(content_frame, text=content, wraplength=400, justify="left")
            content_label.pack(padx=5, pady=5)

            # Button Frame
            button_frame = ttk.Frame(self.top)
            button_frame.pack(pady=(0, 10))

            # Yes Button
            yes_button = ttk.Button(button_frame, text="Yes", command=self.yes_clicked, width=10)
            yes_button.pack(side=tk.LEFT, padx=5)

            # No Button
            no_button = ttk.Button(button_frame, text="No", command=self.no_clicked, width=10)
            no_button.pack(side=tk.LEFT, padx=5)

            # Center the window
            self.top.update_idletasks()
            screen_width = self.top.winfo_screenwidth()
            screen_height = self.top.winfo_screenheight()
            size = tuple(int(_) for _ in self.top.geometry().split('+')[0].split('x'))
            x = screen_width // 2 - size[0] // 2
            y = screen_height // 2 - size[1] // 2
            self.top.geometry(f"+{x}+{y}")

            self.top.protocol("WM_DELETE_WINDOW", self.no_clicked)

            # Make the dialog modal
            self.top.grab_set()
            self.top.wait_window()

        def yes_clicked(self):
            self.result = True
            self.top.destroy()

        def no_clicked(self):
            self.result = False
            self.top.destroy()

    # Get the root window if it exists
    root = tk._get_default_root()

    if not root:
        # Handle the case where there's no existing Tkinter app
        root = tk.Tk()
        root.withdraw()  # Hide the temporary root
        dialog = ScrollableDialog(root, title, header, scrollable_content)
        root.destroy()  # Destroy the temporary root
        return dialog.result

    dialog = ScrollableDialog(root, title, header, scrollable_content)
    return dialog.result

def is_directory_empty(path: Path) -> bool:
    assert path.is_dir()
    assert path.exists()
    
    directory_contents = list(path.iterdir())
    if not directory_contents:
        return True
    
    # also treat the folder as empty if it only contains display file extensions
    if all(file.is_file() and file.suffix.lower() in DISPLAY_FILE_EXTENSIONS for file in path.iterdir()):
        # this might not actually be empty; ask the user to confirm
        user_says_directory_empty = scrollable_askyesno(
            title='Folder Deletion Confirmation',
            header=f'{path} only contains display files, do you want to delete it?',
            scrollable_content='\n'.join(f'\t{file.name}' for file in directory_contents)
        )
        if not user_says_directory_empty:
            return False
        
        # clean up the files to be deleted
        for file in directory_contents:
            file.unlink()
        
        return True

    return False

def delete_empty_directories(target_directory: Path) -> int:
    if target_directory is None:
        return 0
    
    deleted_files = 0
    for directory_to_delete in list(target_directory.rglob(f"*")):
        if not directory_to_delete.is_dir():
            continue
        if is_directory_empty(directory_to_delete):
            directory_to_delete.rmdir()
            deleted_files += 1
    
    return deleted_files

def clean_directory(config: Configuration) -> int:
    return delete_empty_directories(config.target_directory)