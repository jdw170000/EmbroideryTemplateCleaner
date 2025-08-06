# file_cleaner/main.py
import tkinter as tk
import logging
from logging.handlers import RotatingFileHandler

# Set up logging
from embroidery_template_cleaner.core.configuration import LOG_FILE_LOCATION, load_config, save_config
log_handler = RotatingFileHandler(
    filename=LOG_FILE_LOCATION, 
    maxBytes=5*1024*1024, # 5MB
    backupCount=3
)
logging.basicConfig(
    handlers=[log_handler, logging.StreamHandler()], # Also log to console
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from embroidery_template_cleaner.gui.main_window import CleanerMainWindow

VERSION = 'v2.0.0'

def main():
    root = tk.Tk()
    root.title(f"Embroidery Template Cleaner {VERSION}")
    
    try:
        config = load_config()
        app = CleanerMainWindow(master=root, config=config)
        app.pack(padx=10, pady=10)
        
        # Save configuration on exit
        def on_closing():
            save_config(app.config)
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    except Exception as e:
        logging.critical("A fatal error occurred in the main application.", exc_info=True)
        tk.messagebox.showerror("Fatal Error", f"A critical error occurred: {e}\nSee log file for details.")

if __name__ == "__main__":
    main()