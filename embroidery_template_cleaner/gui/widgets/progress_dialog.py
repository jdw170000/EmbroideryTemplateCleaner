import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import time

class ProgressDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.transient(parent)
        self.grab_set()
        self.title("Cleaning in Progress...")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", lambda: messagebox.showwarning("In Progress", "Cleaning operation is running. Please wait."))

        self.timer_label = ttk.Label(self, text="Elapsed Time: 00:00:00", font=("Arial", 10))
        self.timer_label.pack(pady=(10, 5), padx=20)

        self.spinner = ttk.Progressbar(self, mode='indeterminate', length=300)
        self.spinner.pack(pady=5, padx=20)

        self.status_label = ttk.Label(self, text="Initializing...", wraplength=280, justify=tk.LEFT, font=("Arial", 9))
        self.status_label.pack(pady=(5, 10), padx=20, fill=tk.X, expand=True)

        self._start_time = None
        self._timer_id = None
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        parent_x, parent_y = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        parent_width, parent_height = self.parent.winfo_width(), self.parent.winfo_height()
        dialog_width, dialog_height = self.winfo_reqwidth(), self.winfo_reqheight()
        x_pos = parent_x + (parent_width // 2) - (dialog_width // 2)
        y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{x_pos}+{y_pos}")

    def start_operation(self):
        self.spinner.start(15)
        self._start_time = time.time()
        self._update_timer_display()

    def _update_timer_display(self):
        if self._start_time is None: return
        elapsed = int(time.time() - self._start_time)
        h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
        self.timer_label.config(text=f"Elapsed Time: {h:02}:{m:02}:{s:02}")
        self._timer_id = self.after(1000, self._update_timer_display)

    def update_status(self, message):
        self.status_label.config(text=message)

    def stop_operation(self):
        self.spinner.stop()
        if self._timer_id:
            self.after_cancel(self._timer_id)
        self._timer_id = None
        self._start_time = None