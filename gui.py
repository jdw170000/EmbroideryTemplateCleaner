import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox

from pathlib import Path

from cleaner import clean_directory

from config import Configuration

class CleanerGUI(ttk.Frame):
    def __init__(self, config: Configuration, master=None):
        super().__init__(master)
        self.master = master

        self.config = config

        self.create_widgets()

    def create_widgets(self):
        # Directory selection
        ttk.Label(self, text="Target Directory:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.directory_entry = ttk.Entry(self, width=50)
        self.directory_entry.grid(row=0, column=1, padx=10, pady=5)
        if self.config.target_directory:
            self.directory_entry.insert(0, str(self.config.target_directory))
        self.directory_entry.config(state='readonly')
        browse_button = ttk.Button(self, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=2, padx=10, pady=5)

        # Action button
        action_button = ttk.Button(self, text="Remove Empty Folders", command=self.run_cleaner)
        action_button.grid(row=1, column=1, pady=10)


    def update_config_from_gui(self) -> bool:
        target_directory = Path(self.directory_entry.get()) if self.directory_entry.get() else None

        if not target_directory:
            messagebox.showwarning("Input Error", "Please select a target directory.")
            return False
        
        try:
            self.config = Configuration(target_directory=target_directory)
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
        messagebox.showinfo("Operation Complete", f"Deleted {deleted_files} folders from {self.config.target_directory}!")

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.config(state='normal')
            if self.directory_entry.get():
                self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)
            self.directory_entry.config(state='readonly')