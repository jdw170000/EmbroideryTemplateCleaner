import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox

from pathlib import Path

from cleaner import clean_directory

from config import Configuration, TEMPLATE_FILE_EXTENSIONS

class CleanerGUI(ttk.Frame):
    def __init__(self, config: Configuration, master=None):
        super().__init__(master)
        self.master = master

        self.config = config

        self.extension_vars = {ext: tk.BooleanVar(value=ext in self.config.extensions_to_delete) for ext in sorted(TEMPLATE_FILE_EXTENSIONS)}
        self.create_widgets()

    def create_widgets(self):
        # Directory selection
        ttk.Label(self, text="Target Directory:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.directory_entry = ttk.Entry(self, width=50)
        self.directory_entry.grid(row=0, column=1, padx=10, pady=5)
        if self.config.target_directory:
            self.directory_entry.insert(0, str(self.config.target_directory))
        browse_button = ttk.Button(self, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=2, padx=10, pady=5)

        # Extensions selection
        ttk.Label(self, text="Extensions to Delete:").grid(row=1, column=0, padx=10, pady=5, sticky="w")

        for i, ext in enumerate(sorted(TEMPLATE_FILE_EXTENSIONS), start=1):
            checkbox = ttk.Checkbutton(self, text=ext, variable=self.extension_vars[ext])
            checkbox.grid(row=i, column=1, padx=10, sticky="w")

        # Action button
        action_button = ttk.Button(self, text="Delete Selected File Extensions", command=self.run_cleaner)
        action_button.grid(row=i+1, column=1, pady=10)


    def update_config_from_gui(self) -> bool:
        target_directory = Path(self.directory_entry.get())
        selected_extensions = {ext for ext, var in self.extension_vars.items() if var.get()}

        if not target_directory:
            messagebox.showwarning("Input Error", "Please select a target directory.")
            return False
        
        try:
            self.config = Configuration(target_directory=target_directory, extensions_to_delete=selected_extensions)
            return True
        except ValueError as err:
            messagebox.showwarning("Input Error", err)
            return False

    def run_cleaner(self):
        # try to read new configuration from gui
        if not self.update_config_from_gui():
            return 
        
        # actually run the cleaning operation
        deleted_files = clean_directory(config=self.config)

        # success message
        messagebox.showinfo("Operation Complete", f"Deleted {deleted_files} files from {self.config.target_directory}!")

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.delete(0, ttk.END)
            self.directory_entry.insert(0, directory)