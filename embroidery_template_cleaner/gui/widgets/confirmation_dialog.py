import tkinter as tk
import tkinter.ttk as ttk

class ScrollableConfirmationDialog(tk.Toplevel):
    def __init__(self, parent, title, message_intro, items_to_list, message_outro):
        super().__init__(parent)
        self.parent = parent
        self.transient(parent)
        self.title(title)
        self.parent = parent
        self.result = False
        self.resizable(False, False)

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        intro_label = ttk.Label(main_frame, text=message_intro, wraplength=480, justify=tk.LEFT)
        intro_label.pack(pady=(0, 5), anchor="w", fill=tk.X)

        text_area_frame = ttk.Frame(main_frame)
        text_area_frame.pack(pady=5, fill=tk.X)

        text_widget_height = min(15, len(items_to_list) + 1) if items_to_list else 3
        self.text_widget = tk.Text(text_area_frame, wrap=tk.WORD, height=text_widget_height, width=60,
                                   borderwidth=1, relief="sunken", font=("Courier", 9))
        
        scrollbar = ttk.Scrollbar(text_area_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if items_to_list:
            for item in items_to_list:
                self.text_widget.insert(tk.END, f"\t{item}\n")
        else:
            self.text_widget.insert(tk.END, "\t(No items to show)\n")
        self.text_widget.config(state=tk.DISABLED)

        outro_label = ttk.Label(main_frame, text=message_outro, wraplength=480, justify=tk.LEFT)
        outro_label.pack(pady=(5, 10), anchor="w", fill=tk.X)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5,0))
        button_frame.columnconfigure(0, weight=1)

        no_button = ttk.Button(button_frame, text="No", command=self._on_no, width=10)
        no_button.grid(row=0, column=1, padx=5, sticky="e")

        yes_button = ttk.Button(button_frame, text="Yes", command=self._on_yes, width=10)
        yes_button.grid(row=0, column=2, padx=(0,5), sticky="e")
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._center_window()
        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def _center_window(self):
        self.update_idletasks()
        parent_x, parent_y = self.parent.winfo_rootx(), self.parent.winfo_rooty()
        parent_width, parent_height = self.parent.winfo_width(), self.parent.winfo_height()
        dialog_width, dialog_height = self.winfo_reqwidth(), self.winfo_reqheight()
        x_pos = parent_x + (parent_width // 2) - (dialog_width // 2)
        y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{x_pos}+{y_pos}")

    def _on_yes(self): self.result = True; self.destroy()
    def _on_no(self): self.result = False; self.destroy()
    def _on_close(self): self.result = False; self.destroy()