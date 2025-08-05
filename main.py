import tkinter as tk
from gui import CleanerGUI
from config import load_config, save_config

VERSION = 'v1.1.2'

def main():
    root = tk.Tk()
    root.title(f"Embroidery Template Cleaner {VERSION}")
    config = load_config()
    app = CleanerGUI(master=root, config=config)
    app.pack(padx=10, pady=10)
    try:
        root.mainloop()
    finally:
        save_config(app.config)

if __name__ == "__main__":
    main()