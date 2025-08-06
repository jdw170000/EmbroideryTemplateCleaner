import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import queue
import threading
import logging
from pathlib import Path

from ..core.configuration import Configuration, TEMPLATE_FILE_EXTENSIONS
from ..core.events import (
    Event, StatusUpdate, RequestConfirmation, CleaningResult,
    ErrorOccurred, UserConfirmationResponse, RequestRetrySkipAbort, RetrySkipAbortChoice, RetrySkipAbortResponse
)
from ..core.worker import run_cleaning_task
from .widgets.progress_dialog import ProgressDialog
from .widgets.confirmation_dialog import ScrollableConfirmationDialog
from .widgets.retry_dialog import RetryDialog

class CleanerMainWindow(ttk.Frame):
    def __init__(self, master, config: Configuration):
        super().__init__(master)
        self.master = master
        self.config = config
        
        self.update_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.worker_thread = None

        self.extension_vars = {
            ext: tk.BooleanVar(value=ext in config.extensions_to_delete)
            for ext in sorted(TEMPLATE_FILE_EXTENSIONS)
        }
        
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Target Directory:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.directory_entry = ttk.Entry(self, width=50, state='readonly')
        self.directory_entry.grid(row=0, column=1, padx=10, pady=5)
        if self.config.target_directory:
            self.directory_entry.config(state='normal')
            self.directory_entry.insert(0, str(self.config.target_directory))
            self.directory_entry.config(state='readonly')
        
        browse_button = ttk.Button(self, text="Browse", command=self.browse_directory)
        browse_button.grid(row=0, column=2, padx=10, pady=5)

        ext_label = ttk.Label(self, text="Extensions to Delete:")
        ext_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        extensions_frame = ttk.Frame(self)
        extensions_frame.grid(row=1, column=1, sticky="w")
        sorted_exts = sorted(self.extension_vars.keys())
        mid = (len(sorted_exts) + 1) // 2
        for i, ext in enumerate(sorted_exts):
            r, c = (i, 0) if i < mid else (i - mid, 1)
            ttk.Checkbutton(extensions_frame, text=ext, variable=self.extension_vars[ext]).grid(row=r, column=c, padx=(10, 5), sticky="w")

        self.action_button = ttk.Button(self, text="Delete Selected File Extensions", command=self.start_cleaner)
        self.action_button.grid(row=2, column=1, pady=20)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.config(state='normal')
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)
            self.directory_entry.config(state='readonly')

    def update_config_from_gui(self):
        target_dir = Path(self.directory_entry.get()) if self.directory_entry.get() else None
        selected_exts = {ext for ext, var in self.extension_vars.items() if var.get()}
        try:
            self.config = Configuration(target_directory=target_dir, extensions_to_delete=selected_exts)
            return True
        except ValueError as err:
            messagebox.showerror("Invalid Configuration", str(err))
            return False

    def start_cleaner(self):
        if not self.update_config_from_gui():
            return
        
        self.action_button.config(state=tk.DISABLED)
        self.progress_dialog = ProgressDialog(self.master)
        self.progress_dialog.start_operation()

        self.worker_thread = threading.Thread(
            target=run_cleaning_task,
            args=(self.config, self.update_queue, self.response_queue),
            daemon=True
        )
        self.worker_thread.start()
        self.master.after(100, self._process_update_queue)

    def _process_update_queue(self):
        try:
            event: Event = self.update_queue.get_nowait()

            match event:
                case StatusUpdate(message):
                    logging.info(message)
                    if self.progress_dialog: 
                        self.progress_dialog.update_status(message)
                
                case RequestConfirmation(path, files_in_dir):
                    if self.progress_dialog: 
                        self.progress_dialog.withdraw()
                    
                    dialog = ScrollableConfirmationDialog(
                        self.master,
                        title='Confirm Deletion',
                        message_intro=f'The directory "{Path(path).name}" only contains display files:',
                        items_to_list=files_in_dir,
                        message_outro='Do you want to delete the folder and its contents?'
                    )
                    response = UserConfirmationResponse(accepted=dialog.result)
                    logging.info(f"User confirmation for '{path}': {'Accepted' if response.accepted else 'Rejected'}")
                    self.response_queue.put(response)

                    if self.progress_dialog: 
                        self.progress_dialog.deiconify()

                case RequestRetrySkipAbort(op_desc, path, error_msg):
                    if self.progress_dialog: self.progress_dialog.withdraw()

                    dialog = RetryDialog(
                        self.master,
                        title="Operation Failed",
                        description=op_desc,
                        path=path,
                        error=error_msg
                    )
                    response = RetrySkipAbortResponse(choice=dialog.result)
                    self.response_queue.put(response)

                    if self.progress_dialog: 
                        self.progress_dialog.deiconify()

                case CleaningResult(deleted_files_count, target_dir):
                    self.cleanup_ui()
                    logging.info(f"Operation complete. Deleted {deleted_files_count} files.")
                    messagebox.showinfo("Operation Complete", f"Successfully deleted {deleted_files_count} files from {target_dir}!")
                    return # Stop polling

                case ErrorOccurred(message, traceback):
                    self.cleanup_ui()
                    logging.error(f"Error during cleaning: {message}\n{traceback}")
                    messagebox.showerror("Error", message)
                    return # Stop polling
        
        except queue.Empty:
            if not (self.worker_thread and self.worker_thread.is_alive()):
                self.cleanup_ui() # Worker finished unexpectedly

        self.master.after(100, self._process_update_queue)

    def cleanup_ui(self):
        if self.progress_dialog:
            self.progress_dialog.stop_operation()
            self.progress_dialog.destroy()
            self.progress_dialog = None
        self.action_button.config(state=tk.NORMAL)