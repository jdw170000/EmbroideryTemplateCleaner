import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox

from pathlib import Path
import threading
import queue
import time

from cleaner import clean_directory
from config import Configuration, TEMPLATE_FILE_EXTENSIONS

class ScrollableConfirmationDialog(tk.Toplevel):
    def __init__(self, parent, title, message_intro, items_to_list, message_outro):
        super().__init__(parent)
        self.transient(parent) # Appear on top of parent
        self.title(title)
        self.parent = parent
        self.result = False # Default to No
        self.resizable(False, False)

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        intro_label = ttk.Label(main_frame, text=message_intro, wraplength=480, justify=tk.LEFT)
        intro_label.pack(pady=(0, 5), anchor="w", fill=tk.X)

        # Frame for Text widget and Scrollbar
        text_area_frame = ttk.Frame(main_frame)
        text_area_frame.pack(pady=5, fill=tk.X)

        # Text widget for scrollable file list
        # Dynamically set height based on number of items, up to a max of 15 lines
        text_widget_height = min(15, len(items_to_list) + 1) if items_to_list else 3
        self.text_widget = tk.Text(text_area_frame, wrap=tk.WORD, height=text_widget_height, width=60,
                                   borderwidth=1, relief="sunken", font=("Courier", 9)) # Monospace for alignment
        
        scrollbar = ttk.Scrollbar(text_area_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate text widget
        self.text_widget.config(state=tk.NORMAL)
        if items_to_list:
            for item in items_to_list:
                self.text_widget.insert(tk.END, f"\t{item}\n") # Add tab for consistent indent
        else:
            self.text_widget.insert(tk.END, "\t(No specific files listed to confirm)\n")
        self.text_widget.config(state=tk.DISABLED) # Make it read-only

        outro_label = ttk.Label(main_frame, text=message_outro, wraplength=480, justify=tk.LEFT)
        outro_label.pack(pady=(5, 10), anchor="w", fill=tk.X)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5,0))
        
        button_frame.columnconfigure(0, weight=1) # Spacer column to push buttons to the right

        no_button = ttk.Button(button_frame, text="No", command=self._on_no, width=10)
        no_button.grid(row=0, column=1, padx=5, sticky="e")

        yes_button = ttk.Button(button_frame, text="Yes", command=self._on_yes, width=10)
        yes_button.grid(row=0, column=2, padx=(0,5), sticky="e")
        
        self.protocol("WM_DELETE_WINDOW", self._on_close) # Handle 'X' button
        
        self._center_window() # Center dialog on parent
        
        self.grab_set()    # Make modal
        self.focus_set()   # Steal focus
        self.wait_window(self) # Wait for this dialog to be destroyed before returning

    def _center_window(self):
        self.update_idletasks() # Ensure widgets are drawn and sizes (reqwidth/reqheight) are up-to-date
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.winfo_reqwidth()
        dialog_height = self.winfo_reqheight()

        x_pos = parent_x + (parent_width // 2) - (dialog_width // 2)
        y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
        
        # Basic screen boundary check to ensure dialog is visible
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if x_pos + dialog_width > screen_width: x_pos = screen_width - dialog_width
        if y_pos + dialog_height > screen_height: y_pos = screen_height - dialog_height
        if x_pos < 0: x_pos = 0
        if y_pos < 0: y_pos = 0

        self.geometry(f"+{x_pos}+{y_pos}") # Position dialog without changing its size

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()

    def _on_close(self):
        # Default behavior for closing the window via 'X' is 'No'
        self.result = False
        self.destroy()

class ProgressDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set() # Make modal
        self.title("Cleaning in Progress...")
        self.resizable(False, False)
        # Prevent closing with 'X' button while an operation is running.
        # User should wait for completion or an error.
        self.protocol("WM_DELETE_WINDOW", lambda: messagebox.showwarning("In Progress", "Cleaning operation is currently running. Please wait."))

        self.timer_label = ttk.Label(self, text="Elapsed Time: 00:00:00", font=("Arial", 10))
        self.timer_label.pack(pady=(10, 5), padx=20)

        self.spinner = ttk.Progressbar(self, mode='indeterminate', length=300)
        self.spinner.pack(pady=5, padx=20)

        self.status_label = ttk.Label(self, text="Initializing...", wraplength=280, justify=tk.LEFT, font=("Arial", 9))
        self.status_label.pack(pady=(5, 10), padx=20, fill=tk.X, expand=True)

        self._start_time = None
        self._timer_id = None

        # Center the dialog on the parent window
        self.update_idletasks() # Ensure window size is calculated
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x_pos = parent_x + (parent_width // 2) - (dialog_width // 2)
        y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"{dialog_width}x{dialog_height}+{x_pos}+{y_pos}")

    def start_operation(self):
        self.spinner.start(15) # Milliseconds interval for spinner update
        self._start_time = time.time()
        self._update_timer_display()
        self.status_label.config(text="Starting operation...")

    def _update_timer_display(self):
        if self._start_time is None: # Operation stopped
            return
        elapsed_seconds = int(time.time() - self._start_time)
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        self.timer_label.config(text=f"Elapsed Time: {hours:02}:{minutes:02}:{seconds:02}")
        self._timer_id = self.after(1000, self._update_timer_display)

    def update_status(self, message):
        self.status_label.config(text=message)

    def stop_operation(self):
        self.spinner.stop()
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        self._start_time = None


class CleanerGUI(ttk.Frame):
    def __init__(self, config: Configuration, master=None):
        super().__init__(master)
        self.master = master
        self.config = config
        self.extension_vars = {ext: tk.BooleanVar(value=ext in self.config.extensions_to_delete) for ext in sorted(TEMPLATE_FILE_EXTENSIONS)}
        
        self.action_button: ttk.Button = None
        self.progress_dialog: ProgressDialog = None
        self.update_queue: queue.Queue = None
        self.response_queue: queue.Queue = None
        self.worker_thread: threading.Thread = None

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

        # Extensions selection
        ttk.Label(self, text="Extensions to Delete:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        extensions_frame = ttk.Frame(self)
        extensions_frame.grid(row=1, column=1, rowspan=len(TEMPLATE_FILE_EXTENSIONS)//2 +1 , sticky="w")

        # Display checkboxes in two columns
        sorted_exts = sorted(TEMPLATE_FILE_EXTENSIONS)
        num_exts = len(sorted_exts)
        mid_point = (num_exts + 1) // 2

        for i, ext in enumerate(sorted_exts):
            checkbox = ttk.Checkbutton(extensions_frame, text=ext, variable=self.extension_vars[ext])
            if i < mid_point:
                checkbox.grid(row=i, column=0, padx=(10,5), sticky="w")
            else:
                checkbox.grid(row=i - mid_point, column=1, padx=(5,10), sticky="w")
        
        current_row = max(mid_point, num_exts - mid_point) # Row after checkboxes

        # Action button
        self.action_button = ttk.Button(self, text="Delete Selected File Extensions", command=self.run_cleaner)
        self.action_button.grid(row=current_row + 1, column=1, pady=20)

    def update_config_from_gui(self) -> bool:
        target_directory = Path(self.directory_entry.get()) if self.directory_entry.get() else None
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
        if not self.update_config_from_gui():
            return
        
        self.action_button.config(state=tk.DISABLED)

        self.progress_dialog = ProgressDialog(self.master)
        self.progress_dialog.start_operation()

        self.update_queue = queue.Queue()
        self.response_queue = queue.Queue()

        self.worker_thread = threading.Thread(
            target=self._execute_clean_directory_thread,
            args=(self.config, self.update_queue, self.response_queue),
            daemon=True
        )
        self.worker_thread.start()
        self.master.after(100, self._process_update_queue)

    def _execute_clean_directory_thread(self, current_config: Configuration, update_queue: queue.Queue, response_queue: queue.Queue):
        try:
            deleted_files_count = clean_directory(current_config, update_queue, response_queue)
            update_queue.put({'type': 'result', 'deleted_files': deleted_files_count, 'target_dir': str(current_config.target_directory)})
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            update_queue.put({'type': 'error', 'message': str(e), 'traceback': tb_str})

    def _process_update_queue(self):
        # Process all available messages from the worker
        try:
            while True: 
                message = self.update_queue.get_nowait()

                if message['type'] == 'status':
                    if self.progress_dialog:
                        self.progress_dialog.update_status(message['message'])
                
                elif message['type'] == 'confirm_empty_dir':
                    # Hide progress dialog temporarily to show messagebox clearly
                    if self.progress_dialog: 
                        self.progress_dialog.withdraw()

                    path_to_confirm = message['path']
                    files_in_dir = message['files'] 
                    
                    title = 'Folder Deletion Confirmation'
                    message_intro = f'{path_to_confirm} only contains display files:'
                    message_outro = 'Do you want to delete it (the folder and these files)?' 

                    dialog = ScrollableConfirmationDialog(
                        self.master, 
                        title, 
                        message_intro, 
                        files_in_dir, 
                        message_outro
                    )
                    user_response = dialog.result 

                    self.response_queue.put(user_response)
                    
                    if self.progress_dialog: 
                        self.progress_dialog.deiconify() # show progress dialog again

                elif message['type'] == 'result':
                    if self.progress_dialog:
                        self.progress_dialog.stop_operation()
                        self.progress_dialog.destroy()
                        self.progress_dialog = None
                    
                    deleted_files = message['deleted_files']
                    target_dir = message['target_dir']
                    messagebox.showinfo("Operation Complete", f"Deleted {deleted_files} files from {target_dir}!")
                    self.action_button.config(state=tk.NORMAL)
                    return # Stop polling

                elif message['type'] == 'error':
                    if self.progress_dialog:
                        self.progress_dialog.stop_operation()
                        self.progress_dialog.destroy()
                        self.progress_dialog = None
                    
                    messagebox.showerror("Error During Cleaning", f"An error occurred: {message['message']}")
                    self.action_button.config(state=tk.NORMAL)
                    return # Stop polling

        except queue.Empty:
            pass

        # Reschedule if worker is still running
        if self.worker_thread and self.worker_thread.is_alive():
            self.master.after(100, self._process_update_queue)
        elif self.progress_dialog: # Worker finished without sending final message result/error message
            self.progress_dialog.stop_operation()
            self.progress_dialog.destroy()
            self.progress_dialog = None
            self.action_button.config(state=tk.NORMAL)
            messagebox.showwarning("Cleanup Status", "Operation ended, but status is unclear.")


    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_entry.config(state='normal')
            if self.directory_entry.get():
                self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, directory)
            self.directory_entry.config(state='readonly')