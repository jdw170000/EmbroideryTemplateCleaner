import tkinter as tk
from gui import CleanerGUI
from config import Configuration

def main():
    root = tk.Tk()
    root.title("Embroidery Template Cleaner")
    app = CleanerGUI(master=root, config=Configuration(''))
    app.pack(padx=10, pady=10)
    root.mainloop()

if __name__ == "__main__":
    main()