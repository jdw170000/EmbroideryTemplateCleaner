import tkinter as tk
import tkinter.ttk as ttk
from ...core.events import RetrySkipAbortChoice

class RetryDialog(tk.Toplevel):
    def __init__(self, parent, title, description, path, error):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.parent = parent
        self.result = RetrySkipAbortChoice.SKIP  # Default to skipping

        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Message explaining the problem
        header_text = f"An error occurred while {description}:"
        header_label = ttk.Label(main_frame, text=header_text, font=("", 10, "bold"))
        header_label.pack(pady=(0, 5), anchor="w")

        path_label = ttk.Label(main_frame, text=path, wraplength=480, justify=tk.LEFT)
        path_label.pack(pady=(0, 10), anchor="w", padx=10)
        
        error_label = ttk.Label(main_frame, text=f"Error: {error}", wraplength=480, justify=tk.LEFT)
        error_label.pack(pady=(0, 15), anchor="w")

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5,0))
        button_frame.columnconfigure(0, weight=1) # Spacer

        abort_button = ttk.Button(button_frame, text="Abort", command=self._on_abort)
        abort_button.grid(row=0, column=1, padx=5, sticky="e")

        skip_button = ttk.Button(button_frame, text="Skip", command=self._on_skip)
        skip_button.grid(row=0, column=2, padx=5, sticky="e")

        retry_button = ttk.Button(button_frame, text="Retry", command=self._on_retry)
        retry_button.grid(row=0, column=3, padx=5, sticky="e")
        
        self.protocol("WM_DELETE_WINDOW", self._on_skip) # 'X' button means skip
        self._center_window()
        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def _center_window(self):
        # (This function is identical to the one in confirmation_dialog.py)
        self.update_idletasks()
        parent_x, parent_y = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        parent_width, parent_height = self.parent.winfo_width(), self.parent.winfo_height()
        dialog_width, dialog_height = self.winfo_reqwidth(), self.winfo_reqheight()
        x_pos = parent_x + (parent_width // 2) - (dialog_width // 2)
        y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{x_pos}+{y_pos}")

    def _on_retry(self):
        self.result = RetrySkipAbortChoice.RETRY
        self.destroy()

    def _on_skip(self):
        self.result = RetrySkipAbortChoice.SKIP
        self.destroy()

    def _on_abort(self):
        self.result = RetrySkipAbortChoice.ABORT
        self.destroy()